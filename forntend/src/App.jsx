import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './context/LanguageContext';
import { AppDataProvider } from './context/AppDataContext';
import MainLayout from './layouts/MainLayout';
import Dashboard from './pages/Dashboard';
import Fields    from './pages/Fields';
import Voice     from './pages/Voice';
import Sync      from './pages/Sync';
import Offline   from './pages/Offline';
import Settings  from './pages/Settings';
import SchemeChat from './pages/SchemeChat';
import './styles/globals.css';

export default function App() {
  return (
    <LanguageProvider>
      <AppDataProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<MainLayout />}>
              <Route index        element={<Dashboard />} />
              <Route path="fields"   element={<Fields />} />
              <Route path="voice"    element={<Voice />} />
              <Route path="sync"     element={<Sync />} />
              <Route path="offline"  element={<Offline />} />
              <Route path="settings" element={<Settings />} />
              <Route path="scheme-chat" element={<SchemeChat />} />
              <Route path="*"        element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AppDataProvider>
    </LanguageProvider>
  );
}
