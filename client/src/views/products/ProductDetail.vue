<template>
  <div class="app-container">
    <el-card v-loading="loading" class="product-detail-card">
      <template v-if="product">
        <el-row :gutter="24">
          <el-col :span="8">
            <div class="product-image-wrapper">
              <el-image
                :src="product.image_url"
                fit="contain"
                :preview-src-list="[product.image_url || '']"
                class="product-image"
              >
                <div slot="placeholder" class="image-placeholder">
                  <i class="el-icon-picture" />
                </div>
              </el-image>
            </div>
          </el-col>
          <el-col :span="16">
            <h2 class="product-name">{{ product.name }}</h2>
            <div class="product-price-section">
              <span class="current-price">£{{ product.current_price || 'N/A' }}</span>
              <span
                v-if="product.previous_price && product.current_price !== product.previous_price"
                class="previous-price"
              >
                Was £{{ product.previous_price }}
              </span>
            </div>
            <div class="product-meta">
              <el-tag type="info" size="small">
                Shop ID: {{ product.shop_id }}
              </el-tag>
              <el-tag type="info" size="small">
                ID: {{ product.id }}
              </el-tag>
            </div>
            <div class="product-dates">
              <p>Created: {{ formatDate(product.created_at) }}</p>
              <p>Updated: {{ formatDate(product.updated_at) }}</p>
            </div>
            <div class="product-actions">
              <el-button
                :type="isInWatchlist ? 'danger' : 'primary'"
                :loading="watchlistLoading"
                :icon="isInWatchlist ? 'el-icon-star-off' : 'el-icon-star-on'"
                @click="toggleWatchlist"
              >
                {{ isInWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist' }}
              </el-button>
              <el-link :href="product.url" target="_blank" type="primary">
                <i class="el-icon-link" /> View Original
              </el-link>
            </div>
          </el-col>
        </el-row>
      </template>
    </el-card>

    <el-card class="chart-card" v-if="product">
      <template slot="header">
        <div class="chart-header">
          <span>Price History (Last {{ daysRange }} days)</span>
          <el-radio-group v-model="daysRange" size="small" @change="handleDaysChange">
            <el-radio-button :label="7">7 Days</el-radio-button>
            <el-radio-button :label="30">30 Days</el-radio-button>
            <el-radio-button :label="90">90 Days</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="chartRef" class="chart-container" v-loading="loadingChart"></div>
      <el-empty
        v-if="!loadingChart && priceHistory.length === 0"
        description="No price history data available"
      />
    </el-card>

    <el-button
      type="text"
      icon="el-icon-arrow-left"
      class="back-button"
      @click="$router.back()"
    >
      Back to Products
    </el-button>
  </div>
</template>

<script lang="ts">
import { Component, Vue, Ref } from 'vue-property-decorator';
import * as echarts from 'echarts';
import { ECharts } from 'echarts';
import 'echarts/theme/macarons.js';
import { getProduct, getProductPriceHistory } from '@/api/products';
import { NotificationsModule } from '@/store/modules/notifications';
import { IProductData, IPriceHistoryDaily } from '@/api/types';

@Component({
  name: 'ProductDetail'
})
export default class extends Vue {
  @Ref('chartRef') readonly chartRef!: HTMLElement;

  private productId: number = 0;
  private product: IProductData | null = null;
  private loading = false;
  private loadingChart = false;
  private watchlistLoading = false;
  private isInWatchlist = false;
  private daysRange: 7 | 30 | 90 = 30;
  private priceHistory: IPriceHistoryDaily[] = [];
  private chartInstance: ECharts | null = null;

  async created() {
    const id = this.$route.params.id;
    if (id) {
      this.productId = parseInt(id, 10);
      await this.loadProduct();
      await this.checkWatchlist();
      await this.loadPriceHistory();
    }
  }

  beforeDestroy() {
    if (this.chartInstance) {
      this.chartInstance.dispose();
      this.chartInstance = null;
    }
  }

  private async loadProduct() {
    this.loading = true;
    try {
      const { data } = await getProduct(this.productId);
      this.product = data;
    } catch (error) {
      console.error('Failed to load product:', error);
      this.$message.error('Failed to load product');
    } finally {
      this.loading = false;
    }
  }

  private async checkWatchlist() {
    try {
      this.isInWatchlist = await NotificationsModule.CheckWatchlist(this.productId);
    } catch (error) {
      console.error('Failed to check watchlist:', error);
    }
  }

  private async toggleWatchlist() {
    this.watchlistLoading = true;
    try {
      if (this.isInWatchlist) {
        await NotificationsModule.RemoveFromWatchlist(this.productId);
        this.isInWatchlist = false;
        this.$message.success('Removed from watchlist');
      } else {
        await NotificationsModule.AddToWatchlist(this.productId);
        this.isInWatchlist = true;
        this.$message.success('Added to watchlist. You will be notified when price changes more than 10%.');
      }
    } catch (error) {
      console.error('Watchlist operation failed:', error);
      this.$message.error('Failed to update watchlist');
    } finally {
      this.watchlistLoading = false;
    }
  }

  private async loadPriceHistory() {
    this.loadingChart = true;
    try {
      const { data } = await getProductPriceHistory(this.productId, this.daysRange);
      this.priceHistory = data;
      this.$nextTick(() => {
        this.initChart();
      });
    } catch (error) {
      console.error('Failed to load price history:', error);
    } finally {
      this.loadingChart = false;
    }
  }

  private handleDaysChange() {
    this.loadPriceHistory();
  }

  private initChart() {
    if (!this.chartRef) {
      return;
    }

    if (this.chartInstance) {
      this.chartInstance.dispose();
    }

    this.chartInstance = echarts.init(this.chartRef, 'macarons');

    const dates = this.priceHistory.map(item => item.date);
    const minPrices = this.priceHistory.map(item => parseFloat(item.min_price));
    const avgPrices = this.priceHistory.map(item => parseFloat(item.avg_price));
    const maxPrices = this.priceHistory.map(item => parseFloat(item.max_price));

    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = `<div>${params[0].axisValue}</div>`;
          params.forEach((item: any) => {
            result += `<div style="color:${item.color}">${item.seriesName}: £${item.value.toFixed(2)}</div>`;
          });
          return result;
        }
      },
      legend: {
        data: ['Minimum', 'Average', 'Maximum'],
        bottom: 10
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dates,
        axisLabel: {
          rotate: dates.length > 30 ? 45 : 0,
          formatter: (value: string) => {
            if (dates.length > 30) {
              const parts = value.split('-');
              return `${parts[1]}/${parts[2]}`;
            }
            return value;
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '£{value}'
        }
      },
      series: [
        {
          name: 'Minimum',
          type: 'line',
          smooth: true,
          data: minPrices,
          areaStyle: {
            opacity: 0.1
          }
        },
        {
          name: 'Average',
          type: 'line',
          smooth: true,
          data: avgPrices,
          lineStyle: {
            width: 3
          }
        },
        {
          name: 'Maximum',
          type: 'line',
          smooth: true,
          data: maxPrices,
          areaStyle: {
            opacity: 0.1
          }
        }
      ]
    };

    this.chartInstance.setOption(option);

    window.addEventListener('resize', () => {
      if (this.chartInstance) {
        this.chartInstance.resize();
      }
    });
  }

  private formatDate(date: Date): string {
    return new Date(date).toLocaleDateString() + ' ' + new Date(date).toLocaleTimeString();
  }
}
</script>

<style lang="scss" scoped>
.product-detail-card {
  margin-bottom: 20px;
}

.product-image-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 20px;
  min-height: 300px;

  .product-image {
    width: 100%;
    height: 280px;

    >>> img {
      object-fit: contain;
    }
  }

  .image-placeholder {
    color: #c0c4cc;
    font-size: 64px;
  }
}

.product-name {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 20px 0;
  line-height: 1.4;
}

.product-price-section {
  margin-bottom: 20px;

  .current-price {
    font-size: 28px;
    font-weight: bold;
    color: #f56c6c;
  }

  .previous-price {
    font-size: 16px;
    color: #909399;
    text-decoration: line-through;
    margin-left: 12px;
  }
}

.product-meta {
  margin-bottom: 15px;

  .el-tag {
    margin-right: 8px;
  }
}

.product-dates {
  color: #909399;
  font-size: 12px;
  margin-bottom: 20px;

  p {
    margin: 4px 0;
  }
}

.product-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.chart-card {
  margin-bottom: 20px;

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .chart-container {
    height: 400px;
    width: 100%;
  }
}

.back-button {
  font-size: 14px;
}
</style>
