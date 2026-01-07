
import { MangaSeries, Comment, Review } from './types';

export const MOCK_MANGA: MangaSeries = {
  id: 'solo-leveling',
  title: 'Solo Leveling',
  author: 'Chugong',
  description: 'In a world where hunters, humans who possess magical abilities, must battle deadly monsters to protect the human race from certain annihilation...',
  coverImage: 'https://picsum.photos/seed/sl_cover/400/600',
  characters: [
    {
      id: 'c1',
      name: 'Sung Jinwoo',
      role: 'Main Character',
      image: 'https://picsum.photos/seed/jinwoo/100/100',
      description: 'The world\'s weakest hunter who suddenly receives a unique system power.'
    },
    {
      id: 'c2',
      name: 'Kim Sangshik',
      role: 'Side Character',
      image: 'https://picsum.photos/seed/kim/100/100',
      description: 'A seasoned hunter who crossed paths with Jinwoo in the early double dungeon incident.'
    }
  ],
  chapters: [
    {
      id: 'ch1',
      number: 1,
      title: 'E-Rank Hunter',
      pages: Array.from({ length: 5 }, (_, i) => ({
        url: `https://picsum.photos/seed/manga_page_${i}/800/1200`,
        pageNumber: i + 1
      }))
    }
  ]
};

export const MOCK_COMMENTS: Comment[] = [
  {
    id: '1',
    author: 'AriseMaster',
    authorAvatar: 'https://picsum.photos/seed/user1/40/40',
    text: 'This art style is absolutely incredible. The double dungeon scene was pure hype!',
    timestamp: '2 hours ago',
    likes: 124,
    replies: [
      {
        id: '1-1',
        author: 'HunterX',
        authorAvatar: 'https://picsum.photos/seed/user2/40/40',
        text: 'I know right? The pacing is perfect.',
        timestamp: '1 hour ago',
        likes: 12,
        replies: []
      }
    ]
  },
  {
    id: '2',
    author: 'ShadowSovereign',
    authorAvatar: 'https://picsum.photos/seed/user3/40/40',
    text: 'Waiting for chapter 2 already. Jinwoo is about to go crazy!',
    timestamp: '5 hours ago',
    likes: 89,
    replies: []
  }
];

export const MOCK_REVIEWS: Review[] = [
  {
    id: 'r1',
    author: 'MangaCritic99',
    authorAvatar: 'https://picsum.photos/seed/critic1/32/32',
    rating: 5,
    text: 'A masterpiece of the regression genre. The art progression is unmatched.',
    date: 'Oct 20, 2024'
  },
  {
    id: 'r2',
    author: 'ReaderPro',
    authorAvatar: 'https://picsum.photos/seed/critic2/32/32',
    rating: 4,
    text: 'Great story, but side characters could use more depth.',
    date: 'Oct 15, 2024'
  }
];
