import http from '@/utils/request'
import {
  INotificationData,
  IWatchlistItemData,
  IUnreadCount
} from './types';

export const getNotifications = (params: {
  unread_only?: boolean;
  offset?: number;
  limit?: number;
}) =>
  http.request<INotificationData[]>({
    url: '/notifications',
    method: 'get',
    params
  });

export const getUnreadCount = () =>
  http.request<IUnreadCount>({
    url: '/notifications/unread-count',
    method: 'get',
  });

export const markNotificationRead = (notificationId: number) =>
  http.request({
    url: `/notifications/${notificationId}/read`,
    method: 'put',
  });

export const markAllRead = () =>
  http.request<IUnreadCount>({
    url: '/notifications/mark-all-read',
    method: 'put',
  });

export const getWatchlist = () =>
  http.request<IWatchlistItemData[]>({
    url: '/notifications/watchlist',
    method: 'get',
  });

export const addToWatchlist = (productId: number) =>
  http.request<IWatchlistItemData>({
    url: '/notifications/watchlist',
    method: 'post',
    data: { product_id: productId }
  });

export const removeFromWatchlist = (productId: number) =>
  http.request({
    url: `/notifications/watchlist/${productId}`,
    method: 'delete',
  });

export const checkWatchlist = (productId: number) =>
  http.request<{ in_watchlist: boolean }>({
    url: `/notifications/watchlist/check/${productId}`,
    method: 'get',
  });
