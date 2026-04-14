import { useState, useRef, useEffect } from 'react';
import { GoogleGenAI } from "@google/genai";
import { 
  Send, 
  BookOpen, 
  Sparkles, 
  User, 
  Bot, 
  RefreshCw, 
  Library,
  ChevronRight,
  MessageSquare,
  Search,
  Settings,
  X,
  Check,
  Plus,
  Heart,
  Share2,
  Copy,
  CheckCircle2,
  Compass,
  TrendingUp,
  Gem,
  Palette,
  Wind
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import Markdown from 'react-markdown';
import { cn } from './lib/utils';

// --- Types ---
interface Message {
  role: 'user' | 'model';
  content: string;
  timestamp: Date;
}

interface UserPreferences {
  genres: string[];
  authors: string[];
  contentTypes: string[];
}

interface DiscoverItem {
  title: string;
  type: string;
  reason: string;
  isGem: boolean;
}

interface MoodOption {
  id: string;
  label: string;
  prompt: string;
  image: string;
  colors: string[];
  icon: any;
}

// --- Constants ---
const getSystemInstruction = (prefs: UserPreferences) => {
  const prefsContext = `
User Preferences:
- Favorite Genres: ${prefs.genres.length > 0 ? prefs.genres.join(', ') : 'Not specified'}
- Favorite Authors: ${prefs.authors.length > 0 ? prefs.authors.join(', ') : 'Not specified'}
- Preferred Content Types: ${prefs.contentTypes.length > 0 ? prefs.contentTypes.join(', ') : 'Any (Books, Manga, Graphic Novels, Webtoons)'}

Please prioritize these preferences in your recommendations while still being open to suggesting new things if they fit the user's current mood.
`;

  return `You are Lumi, a friendly and enthusiastic book and manga enthusiast. 
Your goal is to be a supportive friend who helps users find their next great read.
Personality traits:
- Warm, empathetic, and encouraging.
- Knowledgeable about Western literature, Japanese manga/light novels, graphic novels, and webtoons.
- Curious about the user's mood, current life situation, and past favorites.
- Uses casual but polite language (like a close friend).
- Occasionally uses subtle book/manga/comic references or emojis to show personality.

${prefsContext}

Guidelines:
1. Always ask clarifying questions if the user's request is vague (e.g., "What kind of vibes are you looking for?").
2. When suggesting, provide 2-3 specific titles with a brief, personalized reason why they'd like it.
3. Format your suggestions clearly using Markdown (bold titles, bullet points).
4. If a user is feeling down, suggest something "healing" or "iyashikei". If they want excitement, suggest something "shonen", "thriller", or an action-packed webtoon.
5. Keep responses concise but meaningful. Don't overwhelm with too many options at once.
6. If the user mentions a specific genre or trope, show excitement!
7. If the user expresses interest in a specific author, or if you recommend an author they might not know, provide a brief (2-3 sentence) engaging biography and list their most notable or influential works.
8. Proactively identify and suggest "hidden gems" (lesser-known but high-quality works). For these titles, explicitly explain *why* they are underrated or fly under the radar (e.g., "It's a small indie publication," "It was overshadowed by a bigger release," or "Its unique art style makes it a niche favorite"). Make the user feel like they're discovering a secret treasure.
9. Aim for diversity in your suggestions. When providing multiple recommendations, try to include at least one "cross-genre" pick that bridges their interests with something new.
10. Balance respecting the user's stated preferences with introducing them to new horizons. If they love a specific genre, actively suggest a "gateway" title from an adjacent genre (e.g., if they love High Fantasy, suggest a Historical Fiction with mythical elements).
11. Be knowledgeable about different media formats: Books, Manga, Graphic Novels, and Webtoons. If a user has a strong preference for one media type in a certain genre, encourage exploration by suggesting a high-quality work in a *different* media type within that same genre (e.g., "Since you love psychological thriller books, you might really enjoy the manga 'Monster'!"). Explain why the different format offers a unique experience.`;
};

const DEFAULT_PREFS: UserPreferences = {
  genres: [],
  authors: [],
  contentTypes: ['book', 'manga']
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'model',
      content: "Hi there! I'm Lumi, your personal reading companion. 📚 Whether you're looking for a cozy manga to curl up with or a mind-bending novel, I'm here to help. What's on your mind today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPrefsOpen, setIsPrefsOpen] = useState(false);
  const [isDiscoverOpen, setIsDiscoverOpen] = useState(false);
  const [isMoodPickerOpen, setIsMoodPickerOpen] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(() => !localStorage.getItem('lumi_prefs'));
  const [onboardingStep, setOnboardingStep] = useState(1);
  const [discoverItems, setDiscoverItems] = useState<DiscoverItem[]>([]);
  const [isDiscoverLoading, setIsDiscoverLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' } | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>(() => {
    const saved = localStorage.getItem('lumi_prefs');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Migration: If old 'contentType' exists but not 'contentTypes', convert it
        if (!parsed.contentTypes && parsed.contentType) {
          parsed.contentTypes = parsed.contentType === 'both' ? ['book', 'manga'] : [parsed.contentType];
        }
        // Ensure all arrays exist to prevent .length errors
        return {
          ...DEFAULT_PREFS,
          ...parsed,
          genres: parsed.genres || [],
          authors: parsed.authors || [],
          contentTypes: parsed.contentTypes || DEFAULT_PREFS.contentTypes
        };
      } catch (e) {
        console.error("Error parsing preferences:", e);
        return DEFAULT_PREFS;
      }
    }
    return DEFAULT_PREFS;
  });

  const scrollRef = useRef<HTMLDivElement>(null);
  const chatInstance = useRef<any>(null);

  // Initialize Gemini Chat
  const initChat = () => {
    const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    chatInstance.current = ai.chats.create({
      model: "gemini-3-flash-preview",
      config: {
        systemInstruction: getSystemInstruction(preferences),
      },
    });
  };

  useEffect(() => {
    initChat();
  }, []);

  // Persist preferences and re-init chat when they change
  useEffect(() => {
    localStorage.setItem('lumi_prefs', JSON.stringify(preferences));
    // We don't necessarily want to wipe the chat history when prefs change, 
    // but the next message should use the new system instruction.
    // In Gemini SDK, systemInstruction is set at creation.
    // For a better experience, we'll re-init the chat instance.
    initChat();
  }, [preferences]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Fetch Discover Weekly items
  const fetchDiscoverWeekly = async () => {
    if (discoverItems.length > 0 || isDiscoverLoading) return;
    
    setIsDiscoverLoading(true);
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-3-flash-preview",
        contents: "Generate a 'Discover Weekly' list of 7 unique reading recommendations. Mix popular trending titles with 3-4 'hidden gems'. Include a mix of Books, Manga, Graphic Novels, and Webtoons. For each, provide: title, type, a brief 2-sentence explanation of why it's recommended, and whether it's a 'hidden gem'. Return ONLY a JSON array of objects with keys: title, type, reason, isGem.",
        config: {
          responseMimeType: "application/json"
        }
      });

      const items = JSON.parse(response.text || "[]");
      setDiscoverItems(items);
    } catch (error) {
      console.error("Error fetching discover weekly:", error);
      setToast({ message: "Failed to load Discover Weekly. Try again later!", type: 'info' });
    } finally {
      setIsDiscoverLoading(false);
    }
  };

  useEffect(() => {
    if (isDiscoverOpen && discoverItems.length === 0) {
      fetchDiscoverWeekly();
    }
  }, [isDiscoverOpen]);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      if (!chatInstance.current) {
        throw new Error("Chat not initialized");
      }

      const response = await chatInstance.current.sendMessage({ message: input });
      const modelMessage: Message = {
        role: 'model',
        content: response.text || "I'm sorry, I couldn't process that. Could you try again?",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, modelMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, {
        role: 'model',
        content: "Oops! Something went wrong on my end. Let's try that again? 😅",
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    "Suggest a cozy manga 🍵",
    "A thriller that'll keep me up 🌙",
    "Something like 'Solo Leveling' 🗡️",
    "Classic literature for beginners 📖",
  ];

  const moodOptions: MoodOption[] = [
    {
      id: 'cozy',
      label: 'Cozy & Warm',
      prompt: "I'm looking for something cozy, warm, and comforting—like a warm cup of tea on a rainy day.",
      image: 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&q=80&w=400',
      colors: ['#f59e0b', '#fef3c7'],
      icon: Heart
    },
    {
      id: 'mysterious',
      label: 'Dark & Mysterious',
      prompt: "I want something dark, mysterious, and perhaps a bit noir or gothic.",
      image: 'https://images.unsplash.com/photo-1509248961158-e54f6934749c?auto=format&fit=crop&q=80&w=400',
      colors: ['#0f172a', '#312e81'],
      icon: Search
    },
    {
      id: 'epic',
      label: 'Epic & Grand',
      prompt: "I'm in the mood for something epic, grand, and full of adventure—a true high fantasy or space opera.",
      image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&q=80&w=400',
      colors: ['#9333ea', '#facc15'],
      icon: Sparkles
    },
    {
      id: 'healing',
      label: 'Healing & Soft',
      prompt: "I need something healing, soft, and gentle—a 'iyashikei' experience to soothe my mind.",
      image: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=400',
      colors: ['#34d399', '#bae6fd'],
      icon: Wind
    },
    {
      id: 'intense',
      label: 'Intense & High-Octane',
      prompt: "I want something intense, high-octane, and action-packed that will keep me on the edge of my seat.",
      image: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&q=80&w=400',
      colors: ['#e11d48', '#22d3ee'],
      icon: TrendingUp
    },
    {
      id: 'melancholic',
      label: 'Melancholic & Poetic',
      prompt: "I'm feeling melancholic and poetic—suggest something with beautiful prose and deep emotional resonance.",
      image: 'https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&q=80&w=400',
      colors: ['#60a5fa', '#cbd5e1'],
      icon: BookOpen
    }
  ];

  const handleShareApp = async () => {
    const shareData = {
      title: 'Lumi: Your Reading Companion',
      text: 'Check out Lumi, a friendly AI that suggests books and manga based on your mood!',
      url: window.location.href,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
        setToast({ message: 'App link copied to clipboard!', type: 'success' });
      }
    } catch (err) {
      console.error('Error sharing:', err);
    }
  };

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setToast({ message: 'Message copied to clipboard!', type: 'success' });
    } catch (err) {
      console.error('Error copying:', err);
    }
  };

  const availableGenres = [
    "Fantasy", "Sci-Fi", "Romance", "Thriller", "Horror", "Mystery", 
    "Historical", "Slice of Life", "Action", "Adventure", "Comedy", 
    "Drama", "Psychological", "Supernatural", "Cyberpunk", "Dystopian"
  ];

  const availableMedia = [
    { id: 'book', label: 'Books', icon: '📖' },
    { id: 'manga', label: 'Manga', icon: '🎨' },
    { id: 'graphic-novel', label: 'Graphic Novels', icon: '🖼️' },
    { id: 'webtoon', label: 'Webtoons', icon: '📱' }
  ];

  return (
    <div className="flex flex-col h-screen bg-slate-50 overflow-hidden">
      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20, x: '-50%' }}
            animate={{ opacity: 1, y: 20, x: '-50%' }}
            exit={{ opacity: 0, y: -20, x: '-50%' }}
            className="fixed top-0 left-1/2 z-[100] px-6 py-3 bg-slate-900 text-white rounded-2xl shadow-2xl flex items-center gap-3 border border-slate-700"
          >
            <CheckCircle2 size={18} className="text-emerald-400" />
            <span className="text-sm font-medium">{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Onboarding Flow */}
      <AnimatePresence>
        {isOnboardingOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[200] flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="bg-white w-full max-w-xl rounded-[32px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-8 pb-4 flex justify-between items-center">
                <div className="flex gap-1.5">
                  {[1, 2, 3].map(step => (
                    <div 
                      key={step} 
                      className={cn(
                        "h-1.5 rounded-full transition-all duration-500",
                        onboardingStep >= step ? "w-8 bg-brand-500" : "w-2 bg-slate-200"
                      )}
                    />
                  ))}
                </div>
                <button 
                  onClick={() => setIsOnboardingOpen(false)}
                  className="text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto px-8 py-4 chat-scroll-area">
                <AnimatePresence mode="wait">
                  {onboardingStep === 1 && (
                    <motion.div
                      key="step1"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-6"
                    >
                      <div className="space-y-2">
                        <h2 className="text-3xl font-bold text-slate-900">Welcome to Lumi! 👋</h2>
                        <p className="text-slate-500 leading-relaxed">
                          I'm your personal reading companion. Let's get to know your tastes so I can find the perfect stories for you.
                        </p>
                      </div>
                      
                      <div className="space-y-4">
                        <label className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                          What do you like to read?
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                          {availableMedia.map(media => (
                            <button
                              key={media.id}
                              onClick={() => {
                                const current = preferences.contentTypes;
                                if (current.includes(media.id)) {
                                  setPreferences(prev => ({ ...prev, contentTypes: current.filter(t => t !== media.id) }));
                                } else {
                                  setPreferences(prev => ({ ...prev, contentTypes: [...current, media.id] }));
                                }
                              }}
                              className={cn(
                                "flex flex-col items-center gap-3 p-5 rounded-2xl border-2 transition-all text-center",
                                preferences.contentTypes.includes(media.id)
                                  ? "border-brand-500 bg-brand-50 text-brand-700 shadow-sm"
                                  : "border-slate-100 bg-slate-50 text-slate-600 hover:border-slate-200"
                              )}
                            >
                              <span className="text-3xl">{media.icon}</span>
                              <span className="font-bold text-sm">{media.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {onboardingStep === 2 && (
                    <motion.div
                      key="step2"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-6"
                    >
                      <div className="space-y-2">
                        <h2 className="text-3xl font-bold text-slate-900">Favorite Genres 🎭</h2>
                        <p className="text-slate-500 leading-relaxed">
                          Select the genres that make your heart race or your mind wander.
                        </p>
                      </div>
                      
                      <div className="flex flex-wrap gap-2">
                        {availableGenres.map(genre => (
                          <button
                            key={genre}
                            onClick={() => {
                              const current = preferences.genres;
                              if (current.includes(genre)) {
                                setPreferences(prev => ({ ...prev, genres: current.filter(g => g !== genre) }));
                              } else {
                                setPreferences(prev => ({ ...prev, genres: [...current, genre] }));
                              }
                            }}
                            className={cn(
                              "px-4 py-2 rounded-xl border transition-all text-sm font-medium",
                              preferences.genres.includes(genre)
                                ? "bg-brand-500 border-brand-500 text-white shadow-md shadow-brand-200"
                                : "bg-white border-slate-200 text-slate-600 hover:border-brand-300 hover:text-brand-600"
                            )}
                          >
                            {genre}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {onboardingStep === 3 && (
                    <motion.div
                      key="step3"
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="space-y-6"
                    >
                      <div className="space-y-2">
                        <h2 className="text-3xl font-bold text-slate-900">Any favorite authors? ✍️</h2>
                        <p className="text-slate-500 leading-relaxed">
                          Tell me who you already love, and I'll find more like them.
                        </p>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="flex gap-2">
                          <input 
                            type="text"
                            placeholder="e.g. Haruki Murakami, Junji Ito..."
                            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                const val = (e.target as HTMLInputElement).value.trim();
                                if (val && !preferences.authors.includes(val)) {
                                  setPreferences(prev => ({ ...prev, authors: [...prev.authors, val] }));
                                  (e.target as HTMLInputElement).value = '';
                                }
                              }
                            }}
                          />
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {preferences.authors.map(author => (
                            <div key={author} className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium">
                              {author}
                              <button 
                                onClick={() => setPreferences(prev => ({ ...prev, authors: prev.authors.filter(a => a !== author) }))}
                                className="text-slate-400 hover:text-red-500"
                              >
                                <X size={14} />
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-brand-50 p-6 rounded-2xl border border-brand-100 flex items-center gap-4">
                        <div className="w-12 h-12 bg-brand-500 rounded-xl flex items-center justify-center text-white flex-shrink-0">
                          <Sparkles size={24} />
                        </div>
                        <p className="text-sm text-brand-800 leading-relaxed">
                          Lumi is ready! I'll use these preferences to curate your <strong>Discover Weekly</strong> and personalize our chats.
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="p-8 pt-4 bg-slate-50/50 border-t border-slate-100 flex justify-between items-center">
                {onboardingStep > 1 ? (
                  <button 
                    onClick={() => setOnboardingStep(prev => prev - 1)}
                    className="px-6 py-3 text-slate-500 font-bold hover:text-slate-800 transition-colors"
                  >
                    Back
                  </button>
                ) : (
                  <div />
                )}
                
                <button 
                  onClick={() => {
                    if (onboardingStep < 3) {
                      setOnboardingStep(prev => prev + 1);
                    } else {
                      setIsOnboardingOpen(false);
                      setToast({ message: "Welcome aboard! Lumi is ready to help.", type: 'success' });
                    }
                  }}
                  className="px-8 py-3 bg-brand-500 text-white rounded-xl font-bold shadow-lg shadow-brand-200 hover:bg-brand-600 transition-all flex items-center gap-2"
                >
                  {onboardingStep === 3 ? "Start Exploring" : "Next Step"}
                  <ChevronRight size={18} />
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-brand-500 flex items-center justify-center text-white shadow-lg shadow-brand-200">
            <BookOpen size={22} />
          </div>
          <div>
            <h1 className="font-display font-bold text-lg text-slate-800 leading-tight">Lumi</h1>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-medium text-slate-500">Online & Ready to Read</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setIsDiscoverOpen(true)}
            className="p-2 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-all flex items-center gap-2"
            title="Discover Weekly"
          >
            <Compass size={20} />
            <span className="hidden md:inline text-xs font-medium">Discover</span>
          </button>
          <button 
            onClick={() => setIsMoodPickerOpen(true)}
            className="p-2 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-all flex items-center gap-2"
            title="Mood Selection"
          >
            <Palette size={20} />
            <span className="hidden md:inline text-xs font-medium">Moods</span>
          </button>
          <button 
            onClick={handleShareApp}
            className="p-2 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-all flex items-center gap-2"
            title="Share App"
          >
            <Share2 size={20} />
            <span className="hidden md:inline text-xs font-medium">Share</span>
          </button>
          <button 
            onClick={() => setIsPrefsOpen(true)}
            className="p-2 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-all flex items-center gap-2"
            title="Preferences"
          >
            <Settings size={20} />
            <span className="hidden md:inline text-xs font-medium">Preferences</span>
          </button>
          <button 
            onClick={() => window.location.reload()}
            className="p-2 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-xl transition-all"
            title="Reset Chat"
          >
            <RefreshCw size={20} />
          </button>
        </div>
      </header>

      {/* Discover Weekly Sidebar */}
      <AnimatePresence>
        {isDiscoverOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsDiscoverOpen(false)}
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-40"
            />
            <motion.aside
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white z-50 shadow-2xl flex flex-col"
            >
              <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-brand-100 text-brand-600 rounded-xl flex items-center justify-center">
                    <Compass size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">Discover Weekly</h2>
                    <p className="text-xs text-slate-500 font-medium">Curated by Lumi just for you</p>
                  </div>
                </div>
                <button 
                  onClick={() => setIsDiscoverOpen(false)}
                  className="p-2 hover:bg-slate-200 rounded-full transition-colors text-slate-400"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6 chat-scroll-area">
                {isDiscoverLoading ? (
                  <div className="flex flex-col items-center justify-center h-full space-y-4">
                    <div className="w-12 h-12 border-4 border-brand-200 border-t-brand-500 rounded-full animate-spin" />
                    <p className="text-sm text-slate-500 font-medium animate-pulse">Lumi is curating your list...</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {discoverItems.map((item, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="p-4 rounded-2xl border border-slate-100 bg-white hover:border-brand-200 hover:shadow-md transition-all group"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-bold uppercase tracking-wider">
                              {item.type}
                            </span>
                            {item.isGem ? (
                              <span className="flex items-center gap-1 px-2 py-0.5 bg-brand-50 text-brand-600 rounded text-[10px] font-bold uppercase tracking-wider">
                                <Gem size={10} /> Hidden Gem
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-50 text-amber-600 rounded text-[10px] font-bold uppercase tracking-wider">
                                <TrendingUp size={10} /> Trending
                              </span>
                            )}
                          </div>
                          <button 
                            onClick={() => {
                              setInput(`Tell me more about "${item.title}"`);
                              setIsDiscoverOpen(false);
                            }}
                            className="text-brand-500 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Plus size={18} />
                          </button>
                        </div>
                        <h3 className="font-bold text-slate-900 mb-1">{item.title}</h3>
                        <p className="text-sm text-slate-600 leading-relaxed">{item.reason}</p>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>

              <div className="p-6 bg-slate-50 border-t border-slate-100">
                <button 
                  onClick={() => {
                    setDiscoverItems([]);
                    fetchDiscoverWeekly();
                  }}
                  className="w-full py-3 bg-white border border-slate-200 text-slate-600 rounded-xl text-sm font-bold hover:border-brand-300 hover:text-brand-600 transition-all flex items-center justify-center gap-2"
                >
                  <RefreshCw size={16} className={isDiscoverLoading ? "animate-spin" : ""} />
                  Refresh Recommendations
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Mood Selection Modal */}
      <AnimatePresence>
        {isMoodPickerOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-[200] flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="bg-white w-full max-w-4xl rounded-[32px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-8 pb-4 flex justify-between items-center border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-brand-100 text-brand-600 rounded-xl flex items-center justify-center">
                    <Palette size={24} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-slate-900">What's your mood?</h2>
                    <p className="text-sm text-slate-500">Select a visual vibe for your next recommendation</p>
                  </div>
                </div>
                <button 
                  onClick={() => setIsMoodPickerOpen(false)}
                  className="p-2 hover:bg-slate-100 rounded-full transition-colors text-slate-400"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-8 chat-scroll-area">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {moodOptions.map((mood) => (
                    <motion.button
                      key={mood.id}
                      whileHover={{ y: -4 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        setInput(mood.prompt);
                        setIsMoodPickerOpen(false);
                      }}
                      className="group relative h-64 rounded-3xl overflow-hidden shadow-lg border border-slate-100 flex flex-col text-left transition-all hover:shadow-xl hover:border-brand-200"
                    >
                      <div className="absolute inset-0">
                        <img 
                          src={mood.image} 
                          alt={mood.label}
                          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                          referrerPolicy="no-referrer"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/40 to-transparent" />
                      </div>
                      
                      <div className="absolute top-4 right-4 flex gap-1">
                        {mood.colors.map((color, i) => (
                          <div 
                            key={i} 
                            className="w-3 h-3 rounded-full border border-white/20 shadow-sm" 
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>

                      <div className="mt-auto p-6 relative z-10">
                        <div className="w-10 h-10 bg-white/20 backdrop-blur-md rounded-xl flex items-center justify-center text-white mb-3 group-hover:bg-brand-500 transition-colors">
                          <mood.icon size={20} />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-1 group-hover:text-brand-200 transition-colors">
                          {mood.label}
                        </h3>
                        <p className="text-xs text-slate-300 line-clamp-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                          {mood.prompt}
                        </p>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>

              <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-center">
                <p className="text-xs text-slate-400 font-medium italic">
                  "Books are a uniquely portable magic." — Stephen King
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="flex-1 flex overflow-hidden relative">
        {/* Preferences Modal */}
        <AnimatePresence>
          {isPrefsOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setIsPrefsOpen(false)}
                className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl overflow-hidden"
              >
                <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand-100 text-brand-600 flex items-center justify-center">
                      <Heart size={20} />
                    </div>
                    <div>
                      <h2 className="font-display font-bold text-lg text-slate-800">Your Preferences</h2>
                      <p className="text-xs text-slate-500">Help Lumi understand your taste</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setIsPrefsOpen(false)}
                    className="p-2 hover:bg-white rounded-full transition-colors text-slate-400 hover:text-slate-600"
                  >
                    <X size={20} />
                  </button>
                </div>

                <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto chat-scroll-area">
                  {/* Content Types */}
                  <section>
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 block">
                      I'm interested in...
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {availableMedia.map(media => (
                        <button
                          key={media.id}
                          onClick={() => {
                            const current = preferences.contentTypes;
                            if (current.includes(media.id)) {
                              setPreferences(prev => ({ ...prev, contentTypes: current.filter(t => t !== media.id) }));
                            } else {
                              setPreferences(prev => ({ ...prev, contentTypes: [...current, media.id] }));
                            }
                          }}
                          className={cn(
                            "flex items-center justify-between px-4 py-2.5 rounded-xl border transition-all text-sm font-medium",
                            preferences.contentTypes.includes(media.id)
                              ? "bg-brand-500 border-brand-500 text-white shadow-md shadow-brand-100"
                              : "bg-white border-slate-200 text-slate-600 hover:border-brand-200"
                          )}
                        >
                          <div className="flex items-center gap-2">
                            <span>{media.icon}</span>
                            <span>{media.label}</span>
                          </div>
                          {preferences.contentTypes.includes(media.id) && <Check size={14} />}
                        </button>
                      ))}
                    </div>
                  </section>

                  {/* Favorite Genres */}
                  <section>
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 block">
                      Favorite Genres
                    </label>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {availableGenres.map(genre => (
                        <button
                          key={genre}
                          onClick={() => {
                            const current = preferences.genres;
                            if (current.includes(genre)) {
                              setPreferences(prev => ({ ...prev, genres: current.filter(g => g !== genre) }));
                            } else {
                              setPreferences(prev => ({ ...prev, genres: [...current, genre] }));
                            }
                          }}
                          className={cn(
                            "px-3 py-1.5 rounded-lg border transition-all text-xs font-medium",
                            preferences.genres.includes(genre)
                              ? "bg-brand-500 border-brand-500 text-white shadow-sm"
                              : "bg-white border-slate-200 text-slate-600 hover:border-brand-200"
                          )}
                        >
                          {genre}
                        </button>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <input 
                        type="text" 
                        placeholder="Add a custom genre..."
                        className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const val = e.currentTarget.value.trim();
                            if (val && !preferences.genres.includes(val)) {
                              setPreferences(prev => ({ ...prev, genres: [...prev.genres, val] }));
                              e.currentTarget.value = '';
                            }
                          }
                        }}
                      />
                    </div>
                  </section>

                  {/* Favorite Authors */}
                  <section>
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 block">
                      Favorite Authors
                    </label>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {preferences.authors.map((author) => (
                        <span 
                          key={author}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium border border-slate-200"
                        >
                          {author}
                          <button 
                            onClick={() => setPreferences(prev => ({ ...prev, authors: prev.authors.filter(a => a !== author) }))}
                            className="hover:text-slate-900"
                          >
                            <X size={12} />
                          </button>
                        </span>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <input 
                        type="text" 
                        placeholder="Add an author (e.g. Haruki Murakami)"
                        className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const val = e.currentTarget.value.trim();
                            if (val && !preferences.authors.includes(val)) {
                              setPreferences(prev => ({ ...prev, authors: [...prev.authors, val] }));
                              e.currentTarget.value = '';
                            }
                          }
                        }}
                      />
                    </div>
                  </section>
                </div>

                <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-end">
                  <button
                    onClick={() => setIsPrefsOpen(false)}
                    className="bg-slate-900 text-white px-6 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-slate-200 hover:bg-slate-800 transition-all flex items-center gap-2"
                  >
                    <Check size={18} />
                    Save Preferences
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
        {/* Sidebar - Desktop Only */}
        <aside className="hidden lg:flex w-72 border-r border-slate-200 bg-white flex-col p-6 gap-6">
          <section>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Palette size={14} /> Mood Vibes
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {moodOptions.map((mood) => (
                <button
                  key={mood.id}
                  onClick={() => setInput(mood.prompt)}
                  className="relative h-24 rounded-xl overflow-hidden group border border-slate-100 hover:border-brand-300 transition-all"
                  title={mood.label}
                >
                  <img 
                    src={mood.image} 
                    alt={mood.label}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 bg-slate-900/40 group-hover:bg-brand-900/40 transition-colors" />
                  <div className="absolute inset-0 flex flex-col items-center justify-center p-2 text-center">
                    <mood.icon size={16} className="text-white mb-1" />
                    <span className="text-[10px] font-bold text-white leading-tight uppercase tracking-tighter">
                      {mood.label.split(' ')[0]}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Sparkles size={14} /> Quick Ideas
            </h2>
            <div className="space-y-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => setInput(prompt.split(' ').slice(0, -1).join(' '))}
                  className="w-full text-left p-3 text-sm text-slate-600 hover:text-brand-700 hover:bg-brand-50 rounded-xl transition-all border border-transparent hover:border-brand-100 group"
                >
                  <span className="flex items-center justify-between">
                    {prompt}
                    <ChevronRight size={14} className="opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="mt-auto">
            <div className="p-4 rounded-2xl bg-slate-900 text-white relative overflow-hidden">
              <Library className="absolute -right-4 -bottom-4 text-white/10 w-24 h-24 rotate-12" />
              <h3 className="font-display font-bold mb-1 relative z-10">Reading Tip</h3>
              <p className="text-xs text-slate-300 relative z-10">
                Try asking for "Iyashikei" if you need something to heal your soul today.
              </p>
            </div>
          </section>
        </aside>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-slate-50/50">
          <div 
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 chat-scroll-area"
          >
            <AnimatePresence initial={false}>
              {messages.map((msg, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  className={cn(
                    "flex w-full gap-3",
                    msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                  )}
                >
                  <div className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm",
                    msg.role === 'user' ? "bg-slate-800 text-white" : "bg-brand-500 text-white"
                  )}>
                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>
                  
                  <div className={cn(
                    "max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3 shadow-sm relative group/msg",
                    msg.role === 'user' 
                      ? "bg-slate-900 text-white rounded-tr-none" 
                      : "bg-white text-slate-800 border border-slate-200 rounded-tl-none"
                  )}>
                    <div className="markdown-body">
                      <Markdown>{msg.content}</Markdown>
                    </div>
                    <div className={cn(
                      "flex items-center justify-between mt-2",
                      msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                    )}>
                      <div className="text-[10px] opacity-50">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <button
                        onClick={() => handleCopyMessage(msg.content)}
                        className={cn(
                          "p-1 rounded-md opacity-0 group-hover/msg:opacity-100 transition-opacity",
                          msg.role === 'user' ? "hover:bg-white/10 text-white/50" : "hover:bg-slate-100 text-slate-400"
                        )}
                        title="Copy message"
                      >
                        <Copy size={12} />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {isLoading && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center text-white animate-pulse">
                  <Bot size={16} />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <div className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce" />
                </div>
              </motion.div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 md:p-6 bg-white border-t border-slate-200">
            <div className="max-w-4xl mx-auto relative">
              <div className="flex gap-3">
                <div className="flex-1 relative group">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-500 transition-colors">
                    <MessageSquare size={18} />
                  </div>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Ask Lumi for a recommendation..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-3.5 pl-12 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all placeholder:text-slate-400"
                  />
                </div>
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading}
                  className="bg-brand-500 hover:bg-brand-600 disabled:bg-slate-200 text-white p-3.5 rounded-2xl shadow-lg shadow-brand-200 disabled:shadow-none transition-all flex items-center justify-center"
                >
                  <Send size={20} />
                </button>
              </div>
              <p className="text-[10px] text-center text-slate-400 mt-3">
                Lumi can make mistakes. Always check the reviews before buying! 📚
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
