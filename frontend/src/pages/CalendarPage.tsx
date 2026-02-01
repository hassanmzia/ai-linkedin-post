import { useEffect, useState } from 'react';
import { calendarAPI } from '../services/api';
import type { CalendarEntry } from '../types';
import toast from 'react-hot-toast';
import { format, addMonths, subMonths, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, isSameDay, parseISO } from 'date-fns';

export default function CalendarPage() {
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [showForm, setShowForm] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [form, setForm] = useState({ title: '', description: '', scheduled_date: '', scheduled_time: '', color: '#3B82F6', recurrence: 'none' });

  const load = () => {
    const start = format(startOfMonth(currentMonth), 'yyyy-MM-dd');
    const end = format(endOfMonth(currentMonth), 'yyyy-MM-dd');
    calendarAPI.list({ start, end }).then(({ data }) => setEntries(data.results || data)).catch(() => {});
  };

  useEffect(() => { load(); }, [currentMonth]);

  const days = eachDayOfInterval({ start: startOfMonth(currentMonth), end: endOfMonth(currentMonth) });
  const startPad = startOfMonth(currentMonth).getDay();

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await calendarAPI.create(form);
      toast.success('Entry added');
      setShowForm(false);
      setForm({ title: '', description: '', scheduled_date: '', scheduled_time: '', color: '#3B82F6', recurrence: 'none' });
      load();
    } catch { toast.error('Failed to create'); }
  };

  const toggleComplete = async (entry: CalendarEntry) => {
    try {
      await calendarAPI.update(entry.id, { is_completed: !entry.is_completed });
      load();
    } catch { toast.error('Failed to update'); }
  };

  const deleteEntry = async (id: string) => {
    try { await calendarAPI.delete(id); load(); } catch { toast.error('Failed to delete'); }
  };

  const handleDayClick = (date: Date) => {
    setSelectedDate(format(date, 'yyyy-MM-dd'));
    setForm({ ...form, scheduled_date: format(date, 'yyyy-MM-dd') });
    setShowForm(true);
  };

  const dayEntries = (date: Date) => entries.filter((e) => isSameDay(parseISO(e.scheduled_date), date));

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Content Calendar</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? 'Cancel' : '+ Add Entry'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input type="text" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
              <input type="date" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })}
                className="input-field" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Time (optional)</label>
              <input type="time" value={form.scheduled_time} onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })}
                className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Recurrence</label>
              <select value={form.recurrence} onChange={(e) => setForm({ ...form, recurrence: e.target.value })} className="input-field">
                <option value="none">None</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="biweekly">Bi-weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Color</label>
              <input type="color" value={form.color} onChange={(e) => setForm({ ...form, color: e.target.value })}
                className="w-full h-10 rounded-lg cursor-pointer" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="input-field" rows={2} />
          </div>
          <div className="flex justify-end">
            <button type="submit" className="btn-primary">Add Entry</button>
          </div>
        </form>
      )}

      {/* Calendar */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <button onClick={() => setCurrentMonth(subMonths(currentMonth, 1))} className="btn-secondary text-sm">Prev</button>
          <h2 className="text-lg font-semibold">{format(currentMonth, 'MMMM yyyy')}</h2>
          <button onClick={() => setCurrentMonth(addMonths(currentMonth, 1))} className="btn-secondary text-sm">Next</button>
        </div>

        <div className="grid grid-cols-7 gap-px bg-gray-200 rounded-lg overflow-hidden">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
            <div key={d} className="bg-gray-50 py-2 text-center text-xs font-medium text-gray-500">{d}</div>
          ))}
          {Array.from({ length: startPad }).map((_, i) => (
            <div key={`pad-${i}`} className="bg-white min-h-[80px]" />
          ))}
          {days.map((day) => {
            const de = dayEntries(day);
            return (
              <div key={day.toISOString()}
                onClick={() => handleDayClick(day)}
                className={`bg-white min-h-[80px] p-1 cursor-pointer hover:bg-gray-50 ${isToday(day) ? 'ring-2 ring-linkedin-500 ring-inset' : ''}`}>
                <span className={`text-xs font-medium ${isToday(day) ? 'text-linkedin-500' : 'text-gray-700'}`}>
                  {format(day, 'd')}
                </span>
                <div className="space-y-0.5 mt-1">
                  {de.slice(0, 3).map((entry) => (
                    <div key={entry.id}
                      className={`text-xs px-1 py-0.5 rounded truncate text-white ${entry.is_completed ? 'opacity-50 line-through' : ''}`}
                      style={{ backgroundColor: entry.color }}
                      onClick={(e) => { e.stopPropagation(); toggleComplete(entry); }}>
                      {entry.title}
                    </div>
                  ))}
                  {de.length > 3 && <span className="text-xs text-gray-400">+{de.length - 3} more</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected day entries */}
      {selectedDate && (
        <div className="card">
          <h3 className="font-semibold mb-3">Entries for {selectedDate}</h3>
          {entries.filter((e) => e.scheduled_date === selectedDate).length > 0 ? (
            <div className="space-y-2">
              {entries.filter((e) => e.scheduled_date === selectedDate).map((entry) => (
                <div key={entry.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                    <div>
                      <p className={`font-medium text-sm ${entry.is_completed ? 'line-through text-gray-400' : ''}`}>{entry.title}</p>
                      {entry.description && <p className="text-xs text-gray-500">{entry.description}</p>}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => toggleComplete(entry)} className="text-xs btn-secondary">
                      {entry.is_completed ? 'Undo' : 'Done'}
                    </button>
                    <button onClick={() => deleteEntry(entry.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No entries for this day</p>
          )}
        </div>
      )}
    </div>
  );
}
