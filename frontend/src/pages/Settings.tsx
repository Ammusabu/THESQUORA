import { useAuth } from "../context/AuthContext";

export default function Settings() {
  const { user } = useAuth();
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-1">Settings</h1>
      <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">Your account details.</p>
      <div className="card p-6 space-y-4 text-sm">
        <div><p className="text-slate-500 dark:text-slate-400">Name</p><p className="font-medium">{user?.name}</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">Email</p><p className="font-medium">{user?.email}</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">Role</p><p className="font-medium capitalize">{user?.role}</p></div>
        <div><p className="text-slate-500 dark:text-slate-400">Department</p><p className="font-medium">{user?.department ?? "—"}</p></div>
      </div>
    </div>
  );
}
