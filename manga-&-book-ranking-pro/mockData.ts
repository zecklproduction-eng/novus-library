
import { RankingItem } from './types';

export const MOCK_DATA: RankingItem[] = [
  // --- MANGA ---
  // Manga - Hottest
  {
    id: 'm1',
    rank: 1,
    title: 'Chainsaw Man',
    author: 'Tatsuki Fujimoto',
    description: "Denji's life as a devil hunter takes a wild turn when he merges with his pet devil, Pochita.",
    views: 374339,
    imageUrl: 'https://picsum.photos/seed/chainsaw/400/600',
    languages: ['EN', 'ES', 'FR'],
    type: 'Manga',
    category: 'Hottest'
  },
  {
    id: 'm2',
    rank: 2,
    title: 'One Piece',
    author: 'Eiichiro Oda',
    description: "Monkey D. Luffy sets out on a grand adventure across the seas to become the King of the Pirates.",
    views: 310606,
    imageUrl: 'https://picsum.photos/seed/onepiece/400/600',
    languages: ['EN', 'TH', 'ES'],
    type: 'Manga',
    category: 'Hottest'
  },
  // Manga - Most Popular
  {
    id: 'm_mp1',
    rank: 1,
    title: 'Jujutsu Kaisen',
    author: 'Gege Akutami',
    description: "A boy swallows a cursed finger and enters a world of shamans and curses.",
    views: 520000,
    imageUrl: 'https://picsum.photos/seed/jjk/400/600',
    languages: ['EN', 'JP', 'ES'],
    type: 'Manga',
    category: 'Most Popular'
  },
  // Manga - Ongoing
  {
    id: 'm1_og',
    rank: 1,
    title: 'Boruto: Two Blue Vortex',
    author: 'Masashi Kishimoto',
    description: "The next generation of ninjas faces unprecedented threats in a world transformed by new powers.",
    views: 271392,
    imageUrl: 'https://picsum.photos/seed/boruto/400/600',
    languages: ['EN', 'ID', 'ES'],
    type: 'Manga',
    category: 'Ongoing'
  },
  {
    id: 'm8_og',
    rank: 2,
    title: 'Spy x Family',
    author: 'Tatsuya Endo',
    description: "A master spy, a deadly assassin, and a telepath form a fake family to maintain world peace.",
    views: 185000,
    imageUrl: 'https://picsum.photos/seed/spy/400/600',
    languages: ['EN', 'ES'],
    type: 'Manga',
    category: 'Ongoing'
  },
  // Manga - Completed
  {
    id: 'm7_cp',
    rank: 1,
    title: 'Demon Slayer',
    author: 'Koyoharu Gotouge',
    description: "Tanjiro Kamado embarks on a dangerous quest to turn his sister human again and avenge his family.",
    views: 999999,
    imageUrl: 'https://picsum.photos/seed/demonslayer/400/600',
    languages: ['EN', 'JP', 'ES'],
    type: 'Manga',
    category: 'Completed'
  },
  {
    id: 'm9_cp',
    rank: 2,
    title: 'Naruto',
    author: 'Masashi Kishimoto',
    description: "A young ninja with a sealed demon within him strives to earn the respect of his village.",
    views: 850000,
    imageUrl: 'https://picsum.photos/seed/naruto/400/600',
    languages: ['EN', 'JP'],
    type: 'Manga',
    category: 'Completed'
  },
  // Manga - Most Viewed
  {
    id: 'm_mv1',
    rank: 1,
    title: 'Dragon Ball Super',
    author: 'Akira Toriyama',
    description: "Goku and his friends face cosmic threats that transcend their own universe and challenge the gods.",
    views: 1200000,
    imageUrl: 'https://picsum.photos/seed/dbz/400/600',
    languages: ['EN', 'JP', 'ES'],
    type: 'Manga',
    category: 'Most Viewed'
  },

  // --- BOOKS ---
  // Books - Hottest
  {
    id: 'b1_ht',
    rank: 1,
    title: 'Atomic Habits',
    author: 'James Clear',
    description: "A tiny changes, remarkable results approach to building good habits and breaking bad ones.",
    views: 500000,
    imageUrl: 'https://picsum.photos/seed/habits/400/600',
    languages: ['EN'],
    type: 'Book',
    category: 'Hottest'
  },
  // Books - Most Popular
  {
    id: 'b_mp1',
    rank: 1,
    title: 'Thinking, Fast and Slow',
    author: 'Daniel Kahneman',
    description: "A tour of the mind and explains the two systems that drive the way we think.",
    views: 650000,
    imageUrl: 'https://picsum.photos/seed/thinking/400/600',
    languages: ['EN'],
    type: 'Book',
    category: 'Most Popular'
  },
  // Books - Fiction
  {
    id: 'b1_fi',
    rank: 1,
    title: 'The Great Gatsby',
    author: 'F. Scott Fitzgerald',
    description: "A tragic story of obsession, wealth, and the elusive American Dream in the Roaring Twenties.",
    views: 150200,
    imageUrl: 'https://picsum.photos/seed/gatsby/400/600',
    languages: ['EN', 'FR'],
    type: 'Book',
    category: 'Fiction'
  },
  // Books - Non-Fiction
  {
    id: 'b3_nf',
    rank: 1,
    title: 'Sapiens: A Brief History',
    author: 'Yuval Noah Harari',
    description: "A sweeping narrative of human history, exploring how we became the masters of the planet.",
    views: 120000,
    imageUrl: 'https://picsum.photos/seed/sapiens/400/600',
    languages: ['EN', 'HE'],
    type: 'Book',
    category: 'Non-Fiction'
  },
  // Books - Most Viewed
  {
    id: 'b_mv1',
    rank: 1,
    title: 'The Subtle Art of Not Giving a F*ck',
    author: 'Mark Manson',
    description: "A counterintuitive approach to living a good life by focusing on what truly matters.",
    views: 800000,
    imageUrl: 'https://picsum.photos/seed/subtle/400/600',
    languages: ['EN'],
    type: 'Book',
    category: 'Most Viewed'
  },

  // --- TRENDING ---
  {
    id: 'm6_tr',
    rank: 1,
    title: 'Kaiju No. 8',
    author: 'Naoya Matsumoto',
    description: "A man gets a second chance at his dream after an unexpected transformation turns him into a Kaiju.",
    views: 450000,
    imageUrl: 'https://picsum.photos/seed/kaiju/400/600',
    languages: ['EN', 'JP'],
    type: 'Manga',
    category: 'Trending'
  },
  {
    id: 'b5_tr',
    rank: 1,
    title: 'The Alchemist',
    author: 'Paulo Coelho',
    description: "A young shepherd follows his dreams across the desert to find a hidden treasure and his destiny.",
    views: 210000,
    imageUrl: 'https://picsum.photos/seed/alchemist/400/600',
    languages: ['EN', 'PT'],
    type: 'Book',
    category: 'Trending'
  }
];