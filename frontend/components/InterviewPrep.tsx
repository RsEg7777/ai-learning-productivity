'use client';
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface InterviewPrepProps { authToken: string; }

const InterviewPrep: React.FC<InterviewPrepProps> = ({ authToken }) => {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
  const [role, setRole] = useState(''); const [company, setCompany] = useState('');
  const [difficulty, setDifficulty] = useState('medium'); const [topic, setTopic] = useState('general');
  const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const [questions, setQuestions] = useState<any[]>([]); const [tips, setTips] = useState<string[]>([]);
  const [expandedQ, setExpandedQ] = useState<number|null>(null);
  const [evalMode, setEvalMode] = useState(false); const [selectedQ, setSelectedQ] = useState<any>(null);
  const [answer, setAnswer] = useState(''); const [evalLoading, setEvalLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<any>(null);

  const generate = async () => {
    if (!role.trim()) { setError('Please enter the job role'); return; }
    setLoading(true); setError(''); setQuestions([]); setTips([]);
    try {
      const res = await fetch(`${API_URL}/interview/generate-questions`, {
        method:'POST', headers:{'Content-Type':'application/json','Authorization':`Bearer ${authToken}`},
        body: JSON.stringify({ role, company, difficulty, topic })
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
      const data = await res.json();
      setQuestions(data.questions || []); setTips(data.tips || []);
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  };

  const evaluate = async () => {
    if (!selectedQ || !answer.trim()) { setError('Please write your answer'); return; }
    setEvalLoading(true); setError(''); setEvaluation(null);
    try {
      const res = await fetch(`${API_URL}/interview/evaluate-answer`, {
        method:'POST', headers:{'Content-Type':'application/json','Authorization':`Bearer ${authToken}`},
        body: JSON.stringify({ question: selectedQ.question, answer, role })
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
      const data = await res.json();
      setEvaluation(data);
    } catch (e: any) { setError(e.message); } finally { setEvalLoading(false); }
  };

  const diffColors: Record<string,string> = { easy:'#10b981', medium:'#f59e0b', hard:'#ef4444', technical:'#6366f1', behavioral:'#8b5cf6', system_design:'#06b6d4' };
  const verdictColor = (v:string) => v === 'strong' ? '#10b981' : v === 'adequate' ? '#f59e0b' : '#ef4444';

  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} className="component-container">
      <h2>💼 Interview Prep</h2>
      <p>AI-generated interview questions tailored to your role, with real-time answer evaluation powered by Amazon Bedrock</p>
      {error && <div className="error">⚠️ {error}</div>}

      {!evalMode ? (
        <>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'1rem'}}>
            <div className="form-group">
              <label>Job Role *</label>
              <input value={role} onChange={e=>setRole(e.target.value)} placeholder="e.g. Senior Software Engineer" />
            </div>
            <div className="form-group">
              <label>Company (optional)</label>
              <input value={company} onChange={e=>setCompany(e.target.value)} placeholder="e.g. Google, Amazon, Infosys" />
            </div>
            <div className="form-group">
              <label>Difficulty</label>
              <select value={difficulty} onChange={e=>setDifficulty(e.target.value)}>
                <option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option>
              </select>
            </div>
            <div className="form-group">
              <label>Topic Focus</label>
              <select value={topic} onChange={e=>setTopic(e.target.value)}>
                <option value="general">General</option><option value="algorithms">Algorithms & DS</option>
                <option value="system design">System Design</option><option value="behavioral">Behavioral</option>
                <option value="machine learning">Machine Learning</option><option value="cloud aws">Cloud / AWS</option>
                <option value="react frontend">React / Frontend</option><option value="python">Python</option>
              </select>
            </div>
          </div>
          <button className="btn-primary" onClick={generate} disabled={loading}>
            {loading ? '🤖 Generating Questions...' : '✨ Generate Interview Questions'}
          </button>
          {loading && <div className="loading"><p>Crafting personalised questions with AI...</p></div>}

          {tips.length > 0 && (
            <motion.div initial={{opacity:0}} animate={{opacity:1}} style={{marginTop:'1.5rem',padding:'1rem',background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.25)',borderRadius:'var(--r-lg)'}}>
              <strong style={{color:'#34d399'}}>💡 Interview Tips:</strong>
              <ul style={{marginTop:'.5rem',paddingLeft:'1.25rem'}}>
                {tips.map((t,i) => <li key={i} style={{color:'var(--text-secondary)',fontSize:'.875rem',marginBottom:'.25rem'}}>{t}</li>)}
              </ul>
            </motion.div>
          )}

          {questions.length > 0 && (
            <div style={{marginTop:'2rem',display:'flex',flexDirection:'column',gap:'1rem'}}>
              <h3 style={{color:'var(--text-primary)',fontSize:'1.1rem',fontWeight:700}}>📋 {questions.length} Questions Generated</h3>
              {questions.map((q,i) => (
                <motion.div key={i} initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} transition={{delay:i*.07}}
                  style={{background:'rgba(13,13,36,0.6)',backdropFilter:'blur(12px)',border:'1px solid var(--border-subtle)',borderRadius:'var(--r-lg)',padding:'1.25rem',cursor:'pointer'}}
                  onClick={() => setExpandedQ(expandedQ===i?null:i)}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:'.75rem'}}>
                    <div style={{flex:1}}>
                      <div style={{display:'flex',gap:'.5rem',marginBottom:'.5rem',flexWrap:'wrap'}}>
                        <span style={{padding:'.18rem .55rem',background:`rgba(${q.type==='technical'?'99,102,241':'139,92,246'},0.2)`,color:diffColors[q.type]||'var(--indigo-light)',borderRadius:'99px',fontSize:'.68rem',fontWeight:700,textTransform:'uppercase'}}>{q.type?.replace('_',' ')}</span>
                        <span style={{padding:'.18rem .55rem',background:'rgba(255,255,255,0.05)',color:diffColors[q.difficulty]||'var(--text-secondary)',borderRadius:'99px',fontSize:'.68rem',fontWeight:700,textTransform:'uppercase'}}>{q.difficulty}</span>
                      </div>
                      <p style={{color:'var(--text-primary)',fontWeight:600,lineHeight:1.55}}>{q.question}</p>
                    </div>
                    <div style={{display:'flex',gap:'.5rem',flexShrink:0}}>
                      <motion.button whileHover={{scale:1.05}} whileTap={{scale:.95}}
                        onClick={e=>{e.stopPropagation();setSelectedQ(q);setAnswer('');setEvaluation(null);setEvalMode(true);}}
                        style={{padding:'.4rem .9rem',background:'linear-gradient(135deg,var(--indigo),var(--violet))',border:'none',borderRadius:'var(--r-sm)',color:'#fff',fontSize:'.78rem',fontWeight:700,cursor:'pointer',whiteSpace:'nowrap'}}>
                        Practice ↗
                      </motion.button>
                      <span style={{color:'var(--text-muted)',fontSize:'1.2rem'}}>{expandedQ===i?'▲':'▼'}</span>
                    </div>
                  </div>
                  <AnimatePresence>
                    {expandedQ === i && (
                      <motion.div initial={{opacity:0,height:0}} animate={{opacity:1,height:'auto'}} exit={{opacity:0,height:0}}
                        style={{marginTop:'1rem',paddingTop:'1rem',borderTop:'1px solid var(--border-subtle)'}}>
                        {q.hints?.length>0 && (<div style={{marginBottom:'.75rem'}}><p style={{color:'var(--amber)',fontWeight:600,fontSize:'.82rem',marginBottom:'.4rem'}}>💡 Hints:</p>{q.hints.map((h:string,j:number)=><p key={j} style={{color:'var(--text-secondary)',fontSize:'.84rem'}}>• {h}</p>)}</div>)}
                        {q.model_answer && (<div><p style={{color:'#34d399',fontWeight:600,fontSize:'.82rem',marginBottom:'.4rem'}}>✅ Key Points to Cover:</p><p style={{color:'var(--text-secondary)',fontSize:'.84rem',lineHeight:1.6}}>{q.model_answer}</p></div>)}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              ))}
            </div>
          )}
        </>
      ) : (
        <motion.div initial={{opacity:0}} animate={{opacity:1}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'1.5rem'}}>
            <h3 style={{color:'var(--indigo-light)',fontSize:'1.1rem',fontWeight:700}}>🎯 Practice Mode</h3>
            <button onClick={()=>{setEvalMode(false);setEvaluation(null);setAnswer('');}} style={{background:'var(--bg-glass)',border:'1px solid var(--border-default)',color:'var(--text-primary)',padding:'.4rem 1rem',borderRadius:'var(--r-sm)',cursor:'pointer',fontSize:'.85rem'}}>← Back</button>
          </div>
          {selectedQ && (<div style={{padding:'1.25rem',background:'rgba(99,102,241,0.08)',border:'1px solid rgba(99,102,241,0.25)',borderRadius:'var(--r-lg)',marginBottom:'1.5rem'}}>
            <p style={{color:'var(--text-secondary)',fontSize:'.8rem',marginBottom:'.5rem',fontWeight:600}}>QUESTION</p>
            <p style={{color:'var(--text-primary)',fontWeight:600,lineHeight:1.55,fontSize:'1.05rem'}}>{selectedQ.question}</p>
          </div>)}
          <div className="form-group">
            <label>Your Answer</label>
            <textarea value={answer} onChange={e=>setAnswer(e.target.value)} rows={8}
              placeholder="Write your answer here. Be specific, use the STAR method for behavioral questions..." />
          </div>
          <button className="btn-primary" onClick={evaluate} disabled={evalLoading}>
            {evalLoading ? '🤖 Evaluating...' : '🎯 Evaluate My Answer'}
          </button>
          {evalLoading && <div className="loading"><p>AI is analysing your answer...</p></div>}
          {evaluation && (
            <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} style={{marginTop:'1.5rem',display:'flex',flexDirection:'column',gap:'1rem'}}>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'1.25rem',background:'rgba(13,13,36,0.7)',border:'1px solid var(--border-default)',borderRadius:'var(--r-lg)'}}>
                <div>
                  <p style={{color:'var(--text-secondary)',fontSize:'.78rem',fontWeight:600,marginBottom:'.3rem'}}>SCORE</p>
                  <p style={{fontSize:'2.5rem',fontWeight:800,background:'linear-gradient(135deg,var(--indigo-light),var(--violet-light))',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent'}}>{evaluation.score}/100</p>
                </div>
                <div style={{textAlign:'right'}}>
                  <p style={{color:'var(--text-secondary)',fontSize:'.78rem',fontWeight:600,marginBottom:'.3rem'}}>VERDICT</p>
                  <p style={{fontSize:'1.1rem',fontWeight:700,color:verdictColor(evaluation.verdict),textTransform:'uppercase'}}>{evaluation.verdict?.replace('_',' ')}</p>
                </div>
              </div>
              {evaluation.strengths?.length>0 && (<div style={{padding:'1rem',background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.25)',borderRadius:'var(--r-md)'}}><p style={{color:'#34d399',fontWeight:700,marginBottom:'.5rem'}}>✅ Strengths</p>{evaluation.strengths.map((s:string,i:number)=><p key={i} style={{color:'var(--text-secondary)',fontSize:'.875rem'}}>• {s}</p>)}</div>)}
              {evaluation.improvements?.length>0 && (<div style={{padding:'1rem',background:'rgba(245,158,11,0.08)',border:'1px solid rgba(245,158,11,0.25)',borderRadius:'var(--r-md)'}}><p style={{color:'#fbbf24',fontWeight:700,marginBottom:'.5rem'}}>📈 Improvements</p>{evaluation.improvements.map((s:string,i:number)=><p key={i} style={{color:'var(--text-secondary)',fontSize:'.875rem'}}>• {s}</p>)}</div>)}
              {evaluation.model_answer && (<div style={{padding:'1rem',background:'rgba(99,102,241,0.08)',border:'1px solid rgba(99,102,241,0.25)',borderRadius:'var(--r-md)'}}><p style={{color:'var(--indigo-light)',fontWeight:700,marginBottom:'.5rem'}}>💡 Model Answer Highlights</p><p style={{color:'var(--text-secondary)',fontSize:'.875rem',lineHeight:1.65}}>{evaluation.model_answer}</p></div>)}
              {evaluation.follow_up_questions?.length>0 && (<div style={{padding:'1rem',background:'rgba(139,92,246,0.08)',border:'1px solid rgba(139,92,246,0.25)',borderRadius:'var(--r-md)'}}><p style={{color:'var(--violet-light)',fontWeight:700,marginBottom:'.5rem'}}>🔄 Follow-up Questions</p>{evaluation.follow_up_questions.map((q:string,i:number)=><p key={i} style={{color:'var(--text-secondary)',fontSize:'.875rem',marginBottom:'.25rem'}}>• {q}</p>)}</div>)}
            </motion.div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};
export default InterviewPrep;
