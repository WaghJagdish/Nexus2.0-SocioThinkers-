import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';
import BottomNav from '../components/BottomNav';
import StatusBar from '../components/StatusBar';

export default function MainLayout() {
  return (
    <div className="phone-shell">
      <StatusBar />
      <Navbar />
      <div className="phone-scroll">
        <Outlet />
      </div>
      <BottomNav />
    </div>
  );
}
