
import { MediaType, MediaStatus, Review, Media } from '../types';

export const POPULAR_MEDIA: Media[] = [
  { id: 'm1', type: MediaType.MANGA, title: 'Chainsaw Man', slug: 'chainsaw-man', coverUrl: 'https://picsum.photos/seed/cs/200/300', tags: ['Action', 'Supernatural', 'Dark'] },
  { id: 'm2', type: MediaType.ANIME, title: 'Frieren: Beyond Journey\'s End', slug: 'frieren', coverUrl: 'https://picsum.photos/seed/frieren/200/300', tags: ['Adventure', 'Drama', 'Fantasy'] },
  { id: 'm3', type: MediaType.BOOK, title: 'The Name of the Wind', slug: 'name-of-the-wind', coverUrl: 'https://picsum.photos/seed/notw/200/300', tags: ['Fantasy', 'Literary'] },
  { id: 'm4', type: MediaType.ANIME, title: 'Cowboy Bebop', slug: 'cowboy-bebop', coverUrl: 'https://picsum.photos/seed/bebop/200/300', tags: ['Sci-Fi', 'Action', 'Space'] },
  { id: 'm5', type: MediaType.MANGA, title: 'Berserk', slug: 'berserk', coverUrl: 'https://picsum.photos/seed/berserk/200/300', tags: ['Dark', 'Fantasy', 'Action'] },
  { id: 'm6', type: MediaType.MANGA, title: 'One Piece', slug: 'one-piece', coverUrl: 'https://picsum.photos/seed/op/200/300', tags: ['Adventure', 'Action', 'Fantasy'] },
  { id: 'm7', type: MediaType.ANIME, title: 'Jujutsu Kaisen', slug: 'jjk', coverUrl: 'https://picsum.photos/seed/jjk/200/300', tags: ['Action', 'Supernatural'] },
  { id: 'm8', type: MediaType.BOOK, title: 'Project Hail Mary', slug: 'hail-mary', coverUrl: 'https://picsum.photos/seed/phm/200/300', tags: ['Sci-Fi', 'Space'] },
  { id: 'm9', type: MediaType.BOOK, title: 'Dune', slug: 'dune', coverUrl: 'https://picsum.photos/seed/dune/200/300', tags: ['Sci-Fi', 'Epic'] },
  { id: 'm10', type: MediaType.ANIME, title: 'Cyberpunk: Edgerunners', slug: 'edgerunners', coverUrl: 'https://picsum.photos/seed/edge/200/300', tags: ['Sci-Fi', 'Action', 'Dark'] },
];

export const MOCK_REVIEWS: Review[] = [
  {
    id: '1',
    userId: 'u1',
    user: { id: 'u1', username: 'MangaFan99', avatarUrl: 'https://picsum.photos/seed/user1/100/100' },
    mediaId: 'm1',
    media: POPULAR_MEDIA[0],
    rating: 4.5,
    body: 'The pacing in the latest arc is absolutely insane. Fujimoto is a madman for that twist in chapter 90! <span class="spoiler">Aki deserved better, my heart is broken.</span> Highly recommend to anyone who likes dark shonen.',
    bodyPlain: 'The pacing in the latest arc is absolutely insane. Fujimoto is a madman for that twist in chapter 90! Aki deserved better, my heart is broken. Highly recommend to anyone who likes dark shonen.',
    hasSpoilers: true,
    status: MediaStatus.READING,
    likesCount: 156,
    isLiked: false,
    comments: [
      {
        id: 'c1',
        userId: 'u2',
        user: { id: 'u2', username: 'AnimeWatcherX', avatarUrl: 'https://picsum.photos/seed/user2/100/100' },
        body: 'Totally agree about chapter 90. I was staring at the wall for hours after reading it.',
        createdAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
        likesCount: 12,
        isLiked: false,
        replies: []
      }
    ],
    createdAt: new Date(Date.now() - 1000 * 60 * 120).toISOString(), // 2 hours ago
    updatedAt: new Date().toISOString()
  },
  {
    id: '2',
    userId: 'u2',
    user: { id: 'u2', username: 'AnimeWatcherX', avatarUrl: 'https://picsum.photos/seed/user2/100/100' },
    mediaId: 'm2',
    media: POPULAR_MEDIA[1],
    rating: 5.0,
    body: 'A masterpiece of storytelling and atmosphere. It’s rare to find an anime that handles the passage of time so gracefully. The animation by Madhouse is top-tier.',
    bodyPlain: 'A masterpiece of storytelling and atmosphere. It’s rare to find an anime that handles the passage of time so gracefully. The animation by Madhouse is top-tier.',
    hasSpoilers: false,
    status: MediaStatus.COMPLETED,
    likesCount: 842,
    isLiked: true,
    comments: [],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
    updatedAt: new Date().toISOString()
  },
  {
    id: '3',
    userId: 'u3',
    user: { id: 'u3', username: 'BookWorm', avatarUrl: 'https://picsum.photos/seed/user3/100/100' },
    mediaId: 'm3',
    media: POPULAR_MEDIA[2],
    rating: 4.0,
    body: 'Kvothe is such a compelling protagonist. Rothfuss has a way with words that makes even the mundane parts of the University feel magical. Waiting for book 3 is pain.',
    bodyPlain: 'Kvothe is such a compelling protagonist. Rothfuss has a way with words that makes even the mundane parts of the University feel magical. Waiting for book 3 is pain.',
    hasSpoilers: false,
    status: MediaStatus.COMPLETED,
    likesCount: 45,
    isLiked: false,
    comments: [
      {
        id: 'c2',
        userId: 'u1',
        user: { id: 'u1', username: 'MangaFan99', avatarUrl: 'https://picsum.photos/seed/user1/100/100' },
        body: 'Book 3 exists only in our collective dreams at this point.',
        createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        likesCount: 5,
        isLiked: true,
        replies: []
      }
    ],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(), // 5 hours ago
    updatedAt: new Date().toISOString()
  },
  {
    id: '4',
    userId: 'u4',
    user: { id: 'u4', username: 'RetroGamer', avatarUrl: 'https://picsum.photos/seed/user4/100/100' },
    mediaId: 'm4',
    media: POPULAR_MEDIA[3],
    rating: 5.0,
    body: 'See you space cowboy... This anime is the definition of cool. Every episode is a vibe. The jazz soundtrack is legendary.',
    bodyPlain: 'See you space cowboy... This anime is the definition of cool. Every episode is a vibe. The jazz soundtrack is legendary.',
    hasSpoilers: false,
    status: MediaStatus.COMPLETED,
    likesCount: 1205,
    isLiked: false,
    comments: [],
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(), // 2 days ago
    updatedAt: new Date().toISOString()
  }
];
