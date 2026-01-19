// TypeScript types for GraphQL schema
export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  latitude?: number;
  longitude?: number;
  geocodedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Company {
  id: string;
  name: string;
  parent?: {
    id: string;
    name: string;
  };
}

export interface CreateCustomerInput {
  name: string;
  email: string;
  phone?: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  postalCode: string;
  country?: string;
  visibilityCompanyIds?: string[];
}

export interface CreateCustomerResponse {
  createCustomer: {
    success: boolean;
    customer: {
      id: string;
      name: string;
      email: string;
    };
  };
}
