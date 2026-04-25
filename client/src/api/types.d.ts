import { UserStatus } from './enums';

export interface ITokenData {
  access_token: string
  token_type: string
}

export interface IUserData {
  id: number
  email: string
  first_name: string
  last_name: string
  status: UserStatus
  created_at: Date
  updated_at: Date
  roles?: IRoleData[]
}

export interface IUserCreate {
  email: string
  first_name: string
  last_name: string
  password: string
  status?: UserStatus
}

export interface IUserUpdate {
  email?: string
  first_name?: string
  last_name?: string
  password?: string
  status?: UserStatus
}

export interface IRoleData {
  id: number
  name: string
  description: string
  created_at: Date
  updated_at: Date
}

export interface IRoleCreate {
  name: string
  description: string
}

export interface IRoleUpdate {
  name?: string
  description?: string
}

export interface IShopData {
  id: number
  created_at: Date
  updated_at: Date
  name: string
  url: string
  query_url: string
  render_javascript: boolean
  listing_page_selector: Object
}

export interface IShopCreate {
  name: string
  url: string
  query_url: string
  render_javascript: boolean
  listing_page_selector: Object
}

export interface IShopUpdate {
  name?: string
  url?: string
  query_url?: string
  render_javascript?: boolean
  listing_page_selector?: Object
}

export interface ScrapedItem {
  name: string
  url: string
  price: string
  price_per_unit: string
  image_url: string
}

export interface IShopListings {
  id: number
  name: string
  listings: ScrapedItem[]
}

export interface IProductData {
  id: number
  url: string
  name: string
  image_url?: string
  shop_id: number
  current_price?: string
  previous_price?: string
  created_at: Date
  updated_at: Date
}

export interface IProductCreate {
  url: string
  name: string
  image_url?: string
  shop_id: number
  current_price?: string
}

export interface IPriceHistoryData {
  id: number
  product_id: number
  price: string
  price_per_unit?: string
  recorded_at: Date
  created_at: Date
}

export interface IPriceHistoryDaily {
  date: string
  min_price: string
  avg_price: string
  max_price: string
}

export interface INotificationData {
  id: number
  user_id: number
  title: string
  message: string
  product_id?: number
  is_read: boolean
  notification_type: string
  old_price?: string
  new_price?: string
  price_change_percent?: string
  read_at?: Date
  created_at: Date
  updated_at: Date
}

export interface IWatchlistItemData {
  id: number
  user_id: number
  product_id: number
  is_active: boolean
  product?: IProductData
  created_at: Date
  updated_at: Date
}

export interface IUnreadCount {
  count: number
}
