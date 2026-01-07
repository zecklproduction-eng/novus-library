
import React, { useState } from 'react';
import { Sidebar } from './components/Layout/Sidebar';
import { Navbar } from './components/Layout/Navbar';
import { MangaReader } from './components/Reader/MangaReader';
import { RightPanel } from './components/Sidebar/RightPanel';
import { RatingSection } from './components/Engagement/RatingSection';
import { CommentSection } from './components/Engagement/CommentSection';
import { MOCK_MANGA, MOCK_COMMENTS } from './constants';
import { getAIInsights } from './services/geminiService';
import { Chapter } from './types';

const App: React.FC = () => {
  const [currentChapter, setCurrentChapter] = useState(MOCK_MANGA.chapters[0]);
  const [aiInsights, setAiInsights] = useState<string | null>(null);
  const [isLoadingAI, setIsLoadingAI] = useState(false);

  const currentChapterIndex = MOCK_MANGA.chapters.findIndex(ch => ch.id === currentChapter.id);
  const hasNextChapter = currentChapterIndex < MOCK_MANGA.chapters.length - 1;

  const handleAIInsights = async () => {
    setIsLoadingAI(true);
    const content = `Manga: ${MOCK_MANGA.title}. Chapter ${currentChapter.number}: ${currentChapter.title}. Description: ${MOCK_MANGA.description}`;
    const insights = await getAIInsights(currentChapter.title, content);
    setAiInsights(insights);
    setIsLoadingAI(false);
  };

  const handleChapterSelect = (chapter: Chapter) => {
    setCurrentChapter(chapter);
    setAiInsights(null); // Reset insights when moving to a new chapter
  };

  const handleNextChapter = () => {
    if (hasNextChapter) {
      handleChapterSelect(MOCK_MANGA.chapters[currentChapterIndex + 1]);
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#0b0e14]">
      <Navbar title={MOCK_MANGA.title} />
      
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        
        <main className="flex-1 flex flex-col min-w-0 bg-[#0f172a]/30">
          <div className="flex-1 overflow-y-auto">
            {/* Manga Display Area */}
            <div className="h-[800px] flex flex-col border-b border-slate-800">
               <MangaReader 
                chapter={currentChapter} 
                onAIInsightsClick={handleAIInsights} 
                isLoadingAI={isLoadingAI}
                onNextChapter={handleNextChapter}
                hasNextChapter={hasNextChapter}
              />
            </div>

            {/* Engagement Area */}
            <div className="max-w-4xl mx-auto py-12 px-6">
              <RatingSection />
              <CommentSection comments={MOCK_COMMENTS} />
              
              {/* Footer Spacer */}
              <div className="h-20" />
            </div>
          </div>
        </main>

        <RightPanel 
          series={MOCK_MANGA} 
          activeChapter={currentChapter} 
          aiInsights={aiInsights}
          onChapterSelect={handleChapterSelect}
        />
      </div>
    </div>
  );
};

export default App;
