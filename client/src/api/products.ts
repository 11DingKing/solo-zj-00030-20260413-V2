import http from '@/utils/request'
import {
  IProductData,
  IPriceHistoryDaily,
  IWatchlistItemData
} from './types';

export const getProducts = (params: {
  offset?: number;
  limit?: number;
  min_price?: string;
  max_price?: string;
  sort_by?: string;
  sort_order?: string;
  include?: number[];
}) =>
  http.request<IProductData[]>({
    url: '/products',
    method: 'get',
    params
  });

export const getProduct = (id: number) =>
  http.request<IProductData>({
    url: `/products/${id}`,
    method: 'get',
  });

export const getProductPriceHistory = (id: number, days: number = 30) =>
  http.request<IPriceHistoryDaily[]>({
    url: `/products/${id}/price-history`,
    method: 'get',
    params: { days }
  });

export const syncProductsFromListings = (params: {
  query: string;
  limit?: number;
  include: number[];
}) =>
  http.request<IProductData[]>({
    url: '/products/sync-from-listings',
    method: 'post',
    params
  });
