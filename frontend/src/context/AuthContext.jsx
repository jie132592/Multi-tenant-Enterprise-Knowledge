import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (tenantCode, username, password) => {
    const res = await authAPI.login({ tenant_code: tenantCode, username, password });
    if (res.code === 200) {
      localStorage.setItem('token', res.data.access_token);
      // Fetch user info
      const userRes = await authAPI.getMe();
      if (userRes.code === 200) {
        localStorage.setItem('user', JSON.stringify(userRes.data));
        setUser(userRes.data);
      }
      return { success: true };
    }
    return { success: false, error: res.detail || '登录失败' };
  };

  const register = async (data) => {
    // Convert camelCase to snake_case for API
    const payload = {
      tenant_name: data.tenantName,
      tenant_code: data.tenantCode,
      username: data.username,
      email: data.email,
      password: data.password,
    };
    const res = await authAPI.register(payload);
    if (res.code === 200) {
      return { success: true, data: res.data };
    }
    return { success: false, error: res.detail || '注册失败' };
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const changePassword = async (oldPassword, newPassword) => {
    const res = await authAPI.changePassword({ old_password: oldPassword, new_password: newPassword });
    if (res.code === 200) {
      return { success: true };
    }
    return { success: false, error: res.detail || '修改失败' };
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, changePassword, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
