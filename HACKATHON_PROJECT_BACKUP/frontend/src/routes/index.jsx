import { Route, Routes } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";
import LoginPage from "../features/accounts/LoginPage";
import PermissionsPage from "../features/accounts/PermissionsPage";
import ProfilePage from "../features/accounts/ProfilePage";
import RegisterPage from "../features/accounts/RegisterPage";
import RolesPage from "../features/accounts/RolesPage";
import UsersPage from "../features/accounts/UsersPage";
import DashboardPage from "../features/monitoring/DashboardPage";
import ServerCreatePage from "../features/compute/ServerCreatePage";
import ServerDetailPage from "../features/compute/ServerDetailPage";
import ServerEditPage from "../features/compute/ServerEditPage";
import ServerListPage from "../features/compute/ServerListPage";
import FirewallCreatePage from "../features/network/FirewallCreatePage";
import FirewallDashboardPage from "../features/network/FirewallDashboardPage";
import FirewallEditPage from "../features/network/FirewallEditPage";
import FirewallRulesPage from "../features/network/FirewallRulesPage";
import ApprovalRequestsPage from "../features/network/ApprovalRequestsPage";
import AuditDashboardPage from "../features/audit/AuditDashboardPage";
import AuditDetailPage from "../features/audit/AuditDetailPage";
import BlockchainDashboardPage from "../features/blockchain/BlockchainDashboardPage";
import IntegrityAlertPage from "../features/blockchain/IntegrityAlertPage";
import TransactionHistoryPage from "../features/blockchain/TransactionHistoryPage";
import VerificationPage from "../features/blockchain/VerificationPage";
import AppLayout from "../layouts/AppLayout";
import AuthLayout from "../layouts/AuthLayout";
import NotFoundPage from "../pages/NotFoundPage";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route
          path="/"
          element={
            <ProtectedRoute permission="dashboard:read">
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route path="/profile" element={<ProfilePage />} />
        <Route
          path="/users"
          element={
            <ProtectedRoute permission="user:read">
              <UsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/roles"
          element={
            <ProtectedRoute permission="role:read">
              <RolesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/permissions"
          element={
            <ProtectedRoute permission="permission:read">
              <PermissionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/servers"
          element={
            <ProtectedRoute permission="server:read">
              <ServerListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/servers/new"
          element={
            <ProtectedRoute permission="server:create">
              <ServerCreatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/servers/:id/edit"
          element={
            <ProtectedRoute permission="server:update">
              <ServerEditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/servers/:id"
          element={
            <ProtectedRoute permission="server:read">
              <ServerDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/firewalls"
          element={
            <ProtectedRoute permission="firewall:read">
              <FirewallDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/firewalls/new"
          element={
            <ProtectedRoute permission="firewall:create">
              <FirewallCreatePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/firewalls/:id/edit"
          element={
            <ProtectedRoute permission="firewall:update">
              <FirewallEditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/firewalls/:id"
          element={
            <ProtectedRoute permission="firewall:read">
              <FirewallRulesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/firewall-approvals"
          element={
            <ProtectedRoute permission="firewall:read">
              <ApprovalRequestsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <ProtectedRoute permission="audit:read">
              <AuditDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit/:id"
          element={
            <ProtectedRoute permission="audit:read">
              <AuditDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/blockchain"
          element={
            <ProtectedRoute permission="audit:read">
              <BlockchainDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/blockchain/verify/:id"
          element={
            <ProtectedRoute permission="audit:read">
              <VerificationPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/blockchain/verify"
          element={
            <ProtectedRoute permission="audit:read">
              <VerificationPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/blockchain/transactions"
          element={
            <ProtectedRoute permission="audit:read">
              <TransactionHistoryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/blockchain/alerts"
          element={
            <ProtectedRoute permission="audit:read">
              <IntegrityAlertPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
