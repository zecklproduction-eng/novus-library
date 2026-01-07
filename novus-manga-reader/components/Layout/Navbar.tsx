
import React from 'react';
import { Bell, ChevronDown } from 'lucide-react';

interface NavbarProps {
  title?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title }) => {
  const handleProfileClick = () => {
    alert('User Profile: Reader_1\nStatus: Online\nLevel: 42 Shadow Sovereign\n\nProfile view feature coming soon!');
  };

  return (
    <nav className="h-16 bg-[#0f172a] border-b border-slate-800 flex items-center justify-between px-8 shrink-0">
      <div className="flex items-center gap-10">
        <h1 className="text-2xl font-black tracking-tighter text-white uppercase">
          {title || 'NOVUS'}
        </h1>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
          <a href="#" className="hover:text-white transition-colors">Team Admin</a>
          <a href="#" className="hover:text-white transition-colors">User Management</a>
          <a href="#" className="hover:text-white transition-colors">Reports</a>
          <a href="#" className="hover:text-white transition-colors">Rankings</a>
          <a href="#" className="flex items-center gap-1 hover:text-white transition-colors">
            Help & Info <ChevronDown size={14} />
          </a>
        </div>
      </div>
      
      <div className="flex items-center gap-6">
        <div className="relative cursor-pointer text-slate-400 hover:text-white">
          <Bell size={20} />
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-[#0f172a]" />
        </div>
        <div 
          onClick={handleProfileClick}
          className="w-10 h-10 rounded-full bg-slate-700 border border-slate-600 overflow-hidden cursor-pointer hover:ring-2 hover:ring-sky-500 transition-all active:scale-95"
          title="View Profile"
        >
          <img src="https://picsum.photos/seed/profile/100/100" alt="profile" />
        </div>
      </div>
    </nav>
  );
};
