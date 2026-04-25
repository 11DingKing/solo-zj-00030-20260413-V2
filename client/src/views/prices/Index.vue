<template>
  <div class="app-container">
    <div class="search-prices">
      <div class="search-terms">
        <el-select
          v-model="params.include"
          multiple
          placeholder="Select shops"
          no-data-text="No shops available"
          style="width: 200px"
        >
          <el-option
            v-for="shop in allShops"
            :key="shop.id"
            :label="shop.name"
            :value="shop.id"
          />
        </el-select>
        <el-input
          v-model="params.query"
          placeholder="Query"
          clearable
          style="width: 200px"
        />
        <el-button
          :loading="loading"
          type="primary"
          @click="searchAndSync()"
        >
          Search & Sync
        </el-button>
        <el-button
          :loading="loadingProducts"
          type="success"
          @click="loadProducts()"
        >
          Load Products
        </el-button>
      </div>

      <div class="filter-section" v-if="products.length > 0 || showFilters">
        <el-divider>Filters & Sorting</el-divider>
        
        <div class="filter-row">
          <div class="filter-item">
            <label>Price Range</label>
            <el-slider
              v-model="priceRange"
              range
              :min="minPrice"
              :max="maxPrice"
              :step="1"
              show-input
              show-input-controls
              style="width: 300px"
              @change="handlePriceRangeChange"
            />
          </div>

          <div class="filter-item">
            <label>Sort By</label>
            <el-select
              v-model="params.sort_by"
              placeholder="Select sort"
              @change="loadProducts"
              style="width: 150px"
            >
              <el-option label="ID" value="id" />
              <el-option label="Price" value="price" />
              <el-option label="Updated" value="updated_at" />
              <el-option label="Created" value="created_at" />
            </el-select>
          </div>

          <div class="filter-item">
            <label>Order</label>
            <el-radio-group v-model="params.sort_order" @change="loadProducts">
              <el-radio-button label="desc">
                <i class="el-icon-arrow-down" /> Desc
              </el-radio-button>
              <el-radio-button label="asc">
                <i class="el-icon-arrow-up" /> Asc
              </el-radio-button>
            </el-radio-group>
          </div>

          <div class="filter-item">
            <el-button type="text" @click="resetFilters">
              <i class="el-icon-refresh" /> Reset
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="search-results" v-if="results.length > 0">
      <h3>Live Search Results</h3>
      <el-row
        v-for="shop in results"
        :key="shop.id"
        :gutter="12"
      >
        <h4>{{ shop.name }}</h4>
        <el-col
          v-for="item in shop.listings"
          :key="item.url"
          :span="8"
        >
          <el-card
            class="box-card small"
            shadow="hover"
          >
            <el-row>
              <el-col :span="4">
                <div class="card-img">
                  <el-image
                    style="width: 100px; height: 100px"
                    :src="item.image_url"
                    fit="scale-down"
                    lazy
                  />
                </div>
              </el-col>
            </el-row>

            <el-row class="item-name">
              {{ item.name }}
            </el-row>

            <el-row>
              <span class="item-price">£{{ item.price }}</span>
            </el-row>

            <el-row v-if="item.price_per_unit">
              <span class="item-price-unit">£{{ item.price_per_unit }}</span>
            </el-row>

            <el-row>
              <el-col>
                <el-button
                  type="text"
                  class="button"
                >
                  <el-link
                    :href="item.url"
                    type="primary"
                    target="_blank"
                  >
                    View Item
                  </el-link>
                </el-button>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="products-section" v-if="products.length > 0">
      <h3>Saved Products ({{ products.length }})</h3>
      <p class="filter-info" v-if="appliedFilters">
        <span>Filters applied:</span>
        <span v-if="params.min_price"> Min: £{{ params.min_price }}</span>
        <span v-if="params.max_price"> Max: £{{ params.max_price }}</span>
        <span v-if="params.sort_by"> Sort: {{ params.sort_by }} ({{ params.sort_order }})</span>
      </p>
      <el-row :gutter="12">
        <el-col
          v-for="product in products"
          :key="product.id"
          :span="6"
        >
          <el-card
            class="product-card"
            shadow="hover"
            @click.native="goToProductDetail(product.id)"
          >
            <div class="product-image">
              <el-image
                :src="product.image_url"
                fit="scale-down"
                lazy
              >
                <div slot="placeholder" class="image-placeholder">
                  <i class="el-icon-picture" />
                </div>
              </el-image>
            </div>
            <div class="product-info">
              <div class="product-name">{{ product.name }}</div>
              <div class="product-price">
                <span class="current-price">£{{ product.current_price }}</span>
                <span
                  v-if="product.previous_price && product.current_price !== product.previous_price"
                  class="previous-price"
                >
                  Was £{{ product.previous_price }}
                </span>
              </div>
              <div class="product-updated">
                Updated: {{ formatDate(product.updated_at) }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-empty
      v-if="!loading && !loadingProducts && products.length === 0 && results.length === 0"
      description="No products found. Try searching or syncing from listings."
    />
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { getShopListings } from '@/api/shops';
import { getProducts, syncProductsFromListings } from '@/api/products';
import { IShopListings, IProductData } from '@/api/types';
import { ShopsModule } from '@/store/modules/shops';

@Component({
  name: 'Prices',
  components: {}
})
export default class extends Vue {
  private loading = false;
  private loadingProducts = false;
  private showFilters = false;

  private params = {
    include: [] as number[],
    query: '',
    limit: 10,
    min_price: '',
    max_price: '',
    sort_by: '',
    sort_order: 'desc'
  };

  private priceRange: [number, number] = [0, 100];
  private results: IShopListings[] = [];
  private products: IProductData[] = [];
  private allProducts: IProductData[] = [];

  get allShops() {
    return ShopsModule.shops;
  }

  get appliedFilters() {
    return this.params.min_price || this.params.max_price || this.params.sort_by;
  }

  get minPrice(): number {
    if (this.allProducts.length === 0) return 0;
    const prices = this.allProducts
      .map(p => parseFloat(p.current_price || '0'))
      .filter(p => p > 0);
    return prices.length > 0 ? Math.floor(Math.min(...prices)) : 0;
  }

  get maxPrice(): number {
    if (this.allProducts.length === 0) return 100;
    const prices = this.allProducts
      .map(p => parseFloat(p.current_price || '0'))
      .filter(p => p > 0);
    return prices.length > 0 ? Math.ceil(Math.max(...prices)) + 10 : 100;
  }

  created() {
    this.getData();
  }

  private async getData() {
    await ShopsModule.GetShops({});
  }

  private async searchPrices() {
    this.loading = true;
    const params = new URLSearchParams();
    params.append('query', this.params.query);
    for (const i in this.params.include) {
      params.append('include', this.params.include[i]);
    }
    const { data } = await getShopListings(params);
    this.results = data;
    this.loading = false;
  }

  private async searchAndSync() {
    await this.searchPrices();
    
    if (this.results.length > 0 && this.params.query && this.params.include.length > 0) {
      try {
        const { data } = await syncProductsFromListings({
          query: this.params.query,
          limit: this.params.limit,
          include: this.params.include
        });
        this.$message.success(`Synced ${data.length} products`);
        await this.loadProducts();
      } catch (error) {
        console.error('Sync error:', error);
      }
    }
  }

  private async loadProducts() {
    this.loadingProducts = true;
    try {
      const { data } = await getProducts({
        offset: 0,
        limit: 100,
        min_price: this.params.min_price || undefined,
        max_price: this.params.max_price || undefined,
        sort_by: this.params.sort_by || undefined,
        sort_order: this.params.sort_order,
        include: this.params.include.length > 0 ? this.params.include : undefined
      });
      this.products = data;
      if (!this.params.min_price && !this.params.max_price && !this.params.sort_by) {
        this.allProducts = data;
      }
      if (data.length > 0) {
        this.showFilters = true;
      }
    } catch (error) {
      console.error('Load products error:', error);
    } finally {
      this.loadingProducts = false;
    }
  }

  private handlePriceRangeChange() {
    const [min, max] = this.priceRange;
    this.params.min_price = min > this.minPrice ? min.toString() : '';
    this.params.max_price = max < this.maxPrice ? max.toString() : '';
    this.loadProducts();
  }

  private resetFilters() {
    this.params.min_price = '';
    this.params.max_price = '';
    this.params.sort_by = '';
    this.params.sort_order = 'desc';
    this.priceRange = [this.minPrice, this.maxPrice];
    this.loadProducts();
  }

  private goToProductDetail(productId: number) {
    this.$router.push(`/products/${productId}`);
  }

  private formatDate(date: Date): string {
    return new Date(date).toLocaleDateString();
  }
}
</script>

<style lang="scss" scoped>
.search-prices {
  margin-bottom: 20px;
}

.search-terms {
  max-width: 900px;
  margin: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-section {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin: 10px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;

  label {
    font-weight: 500;
    color: #606266;
    font-size: 12px;
  }
}

.filter-info {
  color: #909399;
  font-size: 12px;
  margin-bottom: 15px;

  span {
    margin-right: 10px;
  }
}

.search-results,
.products-section {
  margin: 20px 0;

  h3, h4 {
    margin-bottom: 15px;
    color: #303133;
  }
}

.box-card {
  margin: 5px;
  max-width: 100rem;

  .item-price {
    font-weight: bold;
    font-size: 18px;
    color: #409eff;
  }

  .item-price-unit {
    font-size: 12px;
    color: #909399;
  }

  .item-name {
    font-weight: 500;
    margin: 8px 0;
    min-height: 40px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

.product-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-2px);
  }

  .product-image {
    height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f7fa;
    border-radius: 4px;

    >>> .el-image {
      width: 100%;
      height: 100%;

      img {
        object-fit: contain;
      }
    }

    .image-placeholder {
      color: #c0c4cc;
      font-size: 48px;
    }
  }

  .product-info {
    padding: 10px 0;
  }

  .product-name {
    font-weight: 500;
    margin-bottom: 8px;
    min-height: 40px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    color: #303133;
  }

  .product-price {
    margin-bottom: 8px;

    .current-price {
      font-weight: bold;
      font-size: 18px;
      color: #f56c6c;
    }

    .previous-price {
      font-size: 12px;
      color: #909399;
      text-decoration: line-through;
      margin-left: 8px;
    }
  }

  .product-updated {
    font-size: 12px;
    color: #909399;
  }
}

.card-img {
  height: auto;
  max-width: 30%;
}

.item {
  size: 50px;
  max-width: 250px;
}
</style>
