import { useMemo } from 'react';
import { useAuth } from '@/auth/AuthContext';
import type { Role } from '@/api/types';

export type Capability =
  | 'household:create'
  | 'household:update'
  | 'household:delete'
  | 'household:import'
  | 'center:create'
  | 'center:update'
  | 'center:delete'
  | 'resource:create'
  | 'resource:update'
  | 'resource:delete'
  | 'incident:create'
  | 'incident:update'
  | 'incident:delete'
  | 'zone:manage'
  | 'allocation:run'
  | 'simulator:run'
  | 'user:create';

const READ_ONLY: readonly Capability[] = [];

const RESPONDER: readonly Capability[] = [
  'household:create',
  'household:update',
  'household:import',
  'center:create',
  'center:update',
  'resource:create',
  'resource:update',
  'incident:create',
  'incident:update',
  'zone:manage',
  'allocation:run',
  'simulator:run',
];

const ADMIN_ONLY: readonly Capability[] = [
  'household:delete',
  'center:delete',
  'resource:delete',
  'incident:delete',
  'user:create',
];

export const CAPABILITIES_BY_ROLE: Record<Role, readonly Capability[]> = {
  viewer: READ_ONLY,
  responder: RESPONDER,
  admin: [...RESPONDER, ...ADMIN_ONLY],
};

export function can(role: Role | null | undefined, capability: Capability): boolean {
  if (!role) return false;
  return CAPABILITIES_BY_ROLE[role].includes(capability);
}

export function usePermissions() {
  const { user, hasRole } = useAuth();
  const role = user?.role ?? null;

  return useMemo(
    () => ({
      role,
      isViewer: role === 'viewer',
      isResponder: role === 'responder',
      isAdmin: role === 'admin',
      can: (capability: Capability) => can(role, capability),
      hasRole,
    }),
    [role, hasRole],
  );
}