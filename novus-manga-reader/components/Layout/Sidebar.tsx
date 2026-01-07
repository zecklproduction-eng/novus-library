
import React from 'react';
import { Home, TrendingUp, Upload, MessageSquare, Layers, Search, User, Folder, LayoutGrid } from 'lucide-react';

const SidebarItem = ({ icon: Icon, active = false }: { icon: any, active?: boolean }) => (
  <div className={`p-3 cursor-pointer transition-all duration-200 rounded-xl group relative ${active ? 'bg-indigo-600/20 text-indigo-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`}>
    <Icon size={22} />
    {active && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-indigo-500 rounded-r-full" />}
  </div>
);

export const Sidebar = () => {
  return (
    <aside className="w-20 bg-[#0f172a] border-r border-slate-800 flex flex-col items-center py-6 gap-6 shrink-0 h-screen">
      <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center mb-4 shadow-[0_0_15px_rgba(255,255,255,0.2)]">
        <LayoutGrid className="text-black" size={24} />
      </div>
      
      <SidebarItem icon={Home} active />
      <SidebarItem icon={TrendingUp} />
      <SidebarItem icon={Upload} />
      <SidebarItem icon={MessageSquare} />
      <SidebarItem icon={Layers} />
      <SidebarItem icon={Search} />
      
      <div className="mt-auto flex flex-col gap-6">
        <SidebarItem icon={User} />
        <SidebarItem icon={Folder} />
      </div>
    </aside>
  );
};
