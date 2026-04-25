<template>
  <div class="navbar">
    <hamburger
      id="hamburger-container"
      :is-active="sidebar.opened"
      class="hamburger-container"
      @toggleClick="toggleSideBar"
    />
    <breadcrumb
      id="breadcrumb-container"
      class="breadcrumb-container"
    />
    <div class="right-menu">
      <template v-if="device !== 'mobile'">
        <header-search class="right-menu-item" />
        <el-dropdown
          class="notification-container right-menu-item hover-effect"
          trigger="click"
          @visible-change="handleNotificationVisible"
        >
          <div class="notification-wrapper">
            <i class="el-icon-bell" />
            <el-badge
              :value="unreadCount"
              :hidden="unreadCount === 0"
              class="notification-badge"
              type="danger"
            />
          </div>
          <el-dropdown-menu
            slot="dropdown"
            class="notification-dropdown"
          >
            <div class="notification-header">
              <span>Notifications</span>
              <el-button
                type="text"
                size="mini"
                @click.stop="handleMarkAllRead"
              >
                Mark all read
              </el-button>
            </div>
            <el-divider style="margin: 0;" />
            <div class="notification-list" v-if="notifications.length > 0">
              <div
                v-for="notification in notifications"
                :key="notification.id"
                class="notification-item"
                :class="{ 'unread': !notification.is_read }"
                @click="handleNotificationClick(notification)"
              >
                <div class="notification-icon">
                  <i :class="getNotificationIcon(notification)" />
                </div>
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-message">{{ notification.message }}</div>
                  <div class="notification-time">
                    {{ formatTime(notification.created_at) }}
                  </div>
                </div>
                <div
                  v-if="!notification.is_read"
                  class="notification-dot"
                />
              </div>
            </div>
            <div
              v-else
              class="no-notifications"
            >
              <i class="el-icon-info" />
              <span>No notifications</span>
            </div>
          </el-dropdown-menu>
        </el-dropdown>
        <error-log class="errLog-container right-menu-item hover-effect" />
        <screenfull class="right-menu-item hover-effect" />
      </template>
      <el-dropdown
        class="avatar-container right-menu-item hover-effect"
        trigger="click"
      >
        <div class="avatar-wrapper">
          <i class="el-icon-user-solid" />
        </div>
        <el-dropdown-menu slot="dropdown">
          <router-link to="/profile/">
            <el-dropdown-item>
              Profile
            </el-dropdown-item>
          </router-link>
          <router-link to="/">
            <el-dropdown-item>
              Dashboard
            </el-dropdown-item>
          </router-link>
          <a
            target="_blank"
            href="https://armour.github.io/vue-typescript-admin-docs/"
          >
            <el-dropdown-item>Docs</el-dropdown-item>
          </a>
          <el-dropdown-item
            divided
            @click.native="logout"
          >
            <span style="display:block;">
              Log Out
            </span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { AppModule } from '@/store/modules/app';
import { UserMeModule } from '@/store/modules/me';
import { NotificationsModule } from '@/store/modules/notifications';
import { INotificationData } from '@/api/types';
import Breadcrumb from '@/components/Breadcrumb/index.vue';
import ErrorLog from '@/components/ErrorLog/index.vue';
import Hamburger from '@/components/Hamburger/index.vue';
import HeaderSearch from '@/components/HeaderSearch/index.vue';
import Screenfull from '@/components/Screenfull/index.vue';

@Component({
  name: 'Navbar',
  components: {
    Breadcrumb,
    ErrorLog,
    Hamburger,
    HeaderSearch,
    Screenfull
  }
})
export default class extends Vue {
  private pollingTimer: number | null = null;

  get sidebar() {
    return AppModule.sidebar;
  }

  get device() {
    return AppModule.device.toString();
  }

  get unreadCount() {
    return NotificationsModule.unreadCount;
  }

  get notifications() {
    return NotificationsModule.notifications;
  }

  async created() {
    this.fetchNotifications();
    this.startPolling();
  }

  beforeDestroy() {
    this.stopPolling();
  }

  private toggleSideBar() {
    AppModule.ToggleSideBar(false);
  }

  private async logout() {
    this.stopPolling();
    await UserMeModule.LogOut();
    this.$router.push(`/login?redirect=${this.$route.fullPath}`);
  }

  private async fetchNotifications() {
    await NotificationsModule.GetUnreadCount();
  }

  private async handleNotificationVisible(visible: boolean) {
    if (visible) {
      await NotificationsModule.GetNotifications({
        unread_only: false,
        offset: 0,
        limit: 10
      });
    }
  }

  private async handleMarkAllRead() {
    await NotificationsModule.MarkAllRead();
    this.$message.success('All notifications marked as read');
  }

  private async handleNotificationClick(notification: INotificationData) {
    if (!notification.is_read) {
      await NotificationsModule.MarkNotificationRead(notification.id);
    }
  }

  private getNotificationIcon(notification: INotificationData): string {
    if (notification.notification_type === 'price_change') {
      const oldPrice = parseFloat(notification.old_price || '0');
      const newPrice = parseFloat(notification.new_price || '0');
      return newPrice < oldPrice ? 'el-icon-arrow-down' : 'el-icon-arrow-up';
    }
    return 'el-icon-bell';
  }

  private formatTime(date: Date): string {
    const d = new Date(date);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    
    if (diff < 60000) {
      return 'Just now';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)} min ago`;
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)} hours ago`;
    } else {
      return d.toLocaleDateString();
    }
  }

  private startPolling() {
    this.pollingTimer = window.setInterval(() => {
      NotificationsModule.GetUnreadCount();
    }, 30000);
  }

  private stopPolling() {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer);
      this.pollingTimer = null;
    }
  }
}
</script>

<style lang="scss" scoped>
.navbar {
  height: 50px;
  overflow: hidden;
  position: relative;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    float: left;
    padding: 0 15px;
    cursor: pointer;
    transition: background 0.3s;
    -webkit-tap-highlight-color: transparent;

    &:hover {
      background: rgba(0, 0, 0, 0.025);
    }
  }

  .breadcrumb-container {
    float: left;
  }

  .errLog-container {
    display: inline-block;
    vertical-align: top;
  }

  .right-menu {
    float: right;
    height: 100%;
    line-height: 50px;

    &:focus {
      outline: none;
    }

    .right-menu-item {
      display: inline-block;
      padding: 0 8px;
      height: 100%;
      font-size: 18px;
      color: #5a5e66;
      vertical-align: text-bottom;
      position: relative;

      &.hover-effect {
        cursor: pointer;
        transition: background 0.3s;

        &:hover {
          background: rgba(0, 0, 0, 0.025);
        }
      }
    }

    .notification-container {
      .notification-wrapper {
        position: relative;
        display: inline-block;
      }

      .notification-badge {
        position: absolute;
        top: 5px;
        right: -5px;
      }
    }

    .avatar-container {
      margin-right: 30px;

      .avatar-wrapper {
        .user-avatar {
          cursor: pointer;
          width: 40px;
          height: 40px;
          border-radius: 10px;
        }

        .el-icon-caret-bottom {
          cursor: pointer;
          position: absolute;
          right: -20px;
          top: 25px;
          font-size: 12px;
        }
      }
    }
  }
}

::v-deep .notification-dropdown {
  width: 350px;
  max-height: 500px;
  overflow-y: auto;
  padding: 0;

  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    font-weight: bold;
  }

  .notification-list {
    max-height: 400px;
    overflow-y: auto;
  }

  .notification-item {
    display: flex;
    padding: 12px 15px;
    cursor: pointer;
    position: relative;
    border-bottom: 1px solid #f0f0f0;

    &:hover {
      background-color: #f5f7fa;
    }

    &.unread {
      background-color: #fafafa;
    }

    .notification-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #ecf5ff;
      color: #409eff;
      margin-right: 12px;
      font-size: 18px;
      flex-shrink: 0;
    }

    .notification-content {
      flex: 1;
      min-width: 0;

      .notification-title {
        font-weight: 500;
        font-size: 14px;
        color: #303133;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .notification-message {
        font-size: 12px;
        color: #606266;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .notification-time {
        font-size: 11px;
        color: #909399;
      }
    }

    .notification-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #409eff;
      position: absolute;
      right: 15px;
      top: 50%;
      transform: translateY(-50%);
    }
  }

  .no-notifications {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: #909399;
    font-size: 14px;

    i {
      font-size: 36px;
      margin-bottom: 10px;
    }
  }
}
</style>
