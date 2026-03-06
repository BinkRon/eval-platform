export interface Provider {
  id: string
  provider_name: string
  api_key_set: boolean
  base_url: string | null
  available_models: string[] | null
  is_active: boolean
}

export interface ProviderCreate {
  provider_name: string
  api_key?: string
  base_url?: string
  available_models?: string[]
  is_active?: boolean
}

export interface ProviderUpdate {
  api_key?: string
  base_url?: string
  available_models?: string[]
  is_active?: boolean
}
