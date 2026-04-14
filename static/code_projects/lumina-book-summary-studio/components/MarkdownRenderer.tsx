
import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const lines = content.split('\n');
  
  // Track IDs to prevent duplicates (must match App.tsx logic)
  const idCounts: Record<string, number> = {};

  const generateId = (text: string) => {
    let baseId = text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-');
    
    if (idCounts[baseId]) {
      idCounts[baseId]++;
      return `${baseId}-${idCounts[baseId]}`;
    } else {
      idCounts[baseId] = 1;
      return baseId;
    }
  };

  const elements: React.ReactNode[] = [];
  
  const flushList = (items: string[], key: string | number) => {
    if (items.length > 0) {
      return (
        <ul key={`list-${key}`} className="list-disc pl-6 mb-4 text-slate-600">
          {items.map((item, idx) => <li key={idx}>{item}</li>)}
        </ul>
      );
    }
    return null;
  };

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith('# ')) {
      const text = trimmed.replace('# ', '');
      const id = generateId(text);
      elements.push(<h1 id={id} key={`h1-${i}`} className="text-3xl font-bold text-slate-900 mt-10 mb-4 border-b pb-2">{text}</h1>);
      i++;
    } else if (trimmed.startsWith('## ')) {
      const text = trimmed.replace('## ', '');
      const id = generateId(text);
      const contentNodes: React.ReactNode[] = [];
      let j = i + 1;
      let innerList: string[] = [];
      
      while (j < lines.length && !lines[j].trim().startsWith('# ') && !lines[j].trim().startsWith('## ')) {
        const innerLine = lines[j].trim();
        if (innerLine.startsWith('### ')) {
            const h3Text = innerLine.replace('### ', '');
            const h3Id = generateId(h3Text);
            const h3ContentNodes: React.ReactNode[] = [];
            let k = j + 1;
            let subList: string[] = [];
            
            while (k < lines.length && !lines[k].trim().startsWith('# ') && !lines[k].trim().startsWith('## ') && !lines[k].trim().startsWith('### ')) {
                const subLine = lines[k].trim();
                if (subLine.startsWith('* ') || subLine.startsWith('- ')) {
                    subList.push(subLine.substring(2));
                } else if (subLine === '') {
                    if (subList.length > 0) h3ContentNodes.push(flushList([...subList], `sublist-${k}`));
                    subList = [];
                } else {
                    if (subList.length > 0) h3ContentNodes.push(flushList([...subList], `sublist-${k}`));
                    subList = [];
                    h3ContentNodes.push(<p key={`p-${k}`} className="text-slate-600 leading-relaxed mb-4">{subLine}</p>);
                }
                k++;
            }
            if (subList.length > 0) h3ContentNodes.push(flushList([...subList], `sublist-end-${k}`));
            
            contentNodes.push(
                <details key={`details-h3-${j}`} className="group mb-4 border border-slate-100 rounded-xl overflow-hidden bg-white shadow-sm transition-all duration-200 hover:border-slate-200">
                    <summary 
                      id={h3Id} 
                      title="Click to expand/collapse"
                      className="list-none cursor-pointer p-4 bg-slate-50/50 hover:bg-slate-50 flex items-center justify-between transition-colors"
                    >
                        <h3 className="text-xl font-medium text-slate-700 m-0">{h3Text}</h3>
                        <svg className="w-5 h-5 text-slate-400 group-open:rotate-180 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                    </summary>
                    <div className="p-4 border-t border-slate-100 bg-white">
                        {h3ContentNodes}
                    </div>
                </details>
            );
            j = k;
            continue;
        } else if (innerLine.startsWith('* ') || innerLine.startsWith('- ')) {
            innerList.push(innerLine.substring(2));
        } else if (innerLine === '') {
            if (innerList.length > 0) contentNodes.push(flushList([...innerList], `innerlist-${j}`));
            innerList = [];
        } else {
            if (innerList.length > 0) contentNodes.push(flushList([...innerList], `innerlist-${j}`));
            innerList = [];
            contentNodes.push(<p key={`p-${j}`} className="text-slate-600 leading-relaxed mb-4">{innerLine}</p>);
        }
        j++;
      }
      if (innerList.length > 0) contentNodes.push(flushList([...innerList], `innerlist-end-${j}`));

      elements.push(
        <details key={`details-h2-${i}`} className="group mb-6 border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-md transition-all duration-300">
          <summary 
            id={id} 
            title="Click to expand/collapse"
            className="list-none cursor-pointer p-5 bg-white hover:bg-slate-50 flex items-center justify-between transition-colors"
          >
            <h2 className="text-2xl font-semibold text-slate-800 m-0">{text}</h2>
            <div className="flex items-center space-x-3">
              <span className="text-xs text-slate-400 uppercase tracking-widest font-bold group-open:hidden">Expand</span>
              <span className="text-xs text-slate-400 uppercase tracking-widest font-bold hidden group-open:inline">Collapse</span>
              <svg className="w-6 h-6 text-indigo-500 group-open:rotate-180 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </summary>
          <div className="p-6 border-t border-slate-100 bg-slate-50/20">
            {contentNodes}
          </div>
        </details>
      );
      i = j;
    } else if (trimmed === '') {
      i++;
    } else {
        let items: string[] = [];
        if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
            items.push(trimmed.substring(2));
            elements.push(flushList(items, `toplist-${i}`));
        } else {
            elements.push(<p key={`p-${i}`} className="text-slate-600 leading-relaxed mb-4">{trimmed}</p>);
        }
        i++;
    }
  }

  return (
    <div className="prose prose-slate max-w-none">
      {elements}
    </div>
  );
};

export default MarkdownRenderer;
