import {
  Action,
  getModule,
  Module,
  Mutation,
  VuexModule
} from "vuex-module-decorators";
import {
  getNotifications,
  getUnreadCount,
  markNotificationRead,
  markAllRead,
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  checkWatchlist
} from "@/api/notifications";
import store from "@/store";
import { INotificationData, IWatchlistItemData } from "@/api/types";

export interface INotificationsState {
  notifications: INotificationData[];
  unreadCount: number;
  watchlist: IWatchlistItemData[];
}

@Module({ dynamic: true, store, name: "notifications" })
class Notifications extends VuexModule implements INotificationsState {
  public notifications: INotificationData[] = [];
  public unreadCount: number = 0;
  public watchlist: IWatchlistItemData[] = [];

  @Mutation
  private SET_NOTIFICATIONS(payload: INotificationData[]) {
    this.notifications = payload;
  }

  @Mutation
  private SET_UNREAD_COUNT(payload: number) {
    this.unreadCount = payload;
  }

  @Mutation
  private SET_WATCHLIST(payload: IWatchlistItemData[]) {
    this.watchlist = payload;
  }

  @Mutation
  private ADD_WATCHLIST_ITEM(payload: IWatchlistItemData) {
    const exists = this.watchlist.find(item => item.id === payload.id);
    if (!exists) {
      this.watchlist.push(payload);
    }
  }

  @Mutation
  private REMOVE_WATCHLIST_ITEM(productId: number) {
    this.watchlist = this.watchlist.filter(item => item.product_id !== productId);
  }

  @Mutation
  private MARK_NOTIFICATION_READ(notificationId: number) {
    const notification = this.notifications.find(n => n.id === notificationId);
    if (notification) {
      notification.is_read = true;
    }
    if (this.unreadCount > 0) {
      this.unreadCount -= 1;
    }
  }

  @Mutation
  private MARK_ALL_READ() {
    this.notifications.forEach(n => n.is_read = true);
    this.unreadCount = 0;
  }

  @Action
  public async GetNotifications(params: {
    unread_only?: boolean;
    offset?: number;
    limit?: number;
  }) {
    const { data } = await getNotifications(params);
    this.SET_NOTIFICATIONS(data);
  }

  @Action
  public async GetUnreadCount() {
    const { data } = await getUnreadCount();
    this.SET_UNREAD_COUNT(data.count);
  }

  @Action
  public async MarkNotificationRead(notificationId: number) {
    await markNotificationRead(notificationId);
    this.MARK_NOTIFICATION_READ(notificationId);
  }

  @Action
  public async MarkAllRead() {
    await markAllRead();
    this.MARK_ALL_READ();
  }

  @Action
  public async GetWatchlist() {
    const { data } = await getWatchlist();
    this.SET_WATCHLIST(data);
  }

  @Action
  public async AddToWatchlist(productId: number) {
    const { data } = await addToWatchlist(productId);
    this.ADD_WATCHLIST_ITEM(data);
  }

  @Action
  public async RemoveFromWatchlist(productId: number) {
    await removeFromWatchlist(productId);
    this.REMOVE_WATCHLIST_ITEM(productId);
  }

  @Action
  public async CheckWatchlist(productId: number): Promise<boolean> {
    const { data } = await checkWatchlist(productId);
    return data.in_watchlist;
  }
}

export const NotificationsModule = getModule(Notifications);
