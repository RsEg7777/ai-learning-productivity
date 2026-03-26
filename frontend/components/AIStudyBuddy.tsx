'use client';
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
const API_URL = () => process.env.NEXT_PUBLIC_API_URL || '';

interface AIStudyBuddyProps { authToken: string; }

const AIStudyBuddy: React.FC<AIStudyBuddyProps> = ({ authToken }) => {
  const [tab, setTab] = useState<'chat'|'path'>('chat');
  const [msgs, setMsgs] = useState<{role:string;content:string}[]>([{ role: 'assistant', content: "Hi! I'm Nova, your AI Study Buddy 🤖✨\n\nI'll help you create learning goals, generate personalised study paths, and keep you motivated. What would you like to learn today?" }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [style, setStyle] = useState<'visual'|'auditory'|'kinesthetic'|'reading'>('visual');
  const [goals, setGoals] = useState<any[]>([]);
  const [showGoalForm, setShowGoalForm] = useState(false);
  const [newGoal, setNewGoal] = useState({ title: '', description: '', targetDate: '' });
  const [insight, setInsight] = useState('');
  const [studyPath, setStudyPath] = useState<any>(null);
  const [pathForm, setPathForm] = useState({ topic: '', currentLevel: 'beginner', targetLevel: 'advanced', hoursPerWeek: 10, knownTopics: '' });
  const [pathLoading, setPathLoading] = useState(false);
  const [expandedMod, setExpandedMod] = useState<number|null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const msg = input; setInput('');
    setMsgs(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const res = await fetch(`${API_URL()}/study-buddy/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ message: msg, context: { learningStyle: style, learningGoals: goals } }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
      const data = await res.json();
      setMsgs(prev => [...prev, { role: 'assistant', content: data.response }]);
      if (data.recommendation) setInsight(data.recommendation);
    } catch (e: any) { setMsgs(prev => [...prev, { role: 'assistant', content: `❌ ${e.message}` }]); }
    finally { setLoading(false); }
  };

  const createGoal = async () => {
    if (!newGoal.title || !newGoal.targetDate) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL()}/study-buddy/create-goal`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ ...newGoal, learningStyle: style }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
      const data = await res.json();
      setGoals(prev => [...prev, data.goal]);
      setShowGoalForm(false); setNewGoal({ title:'', description:'', targetDate:'' });
      setMsgs(prev => [...prev, { role: 'assistant', content: `🎯 Goal "${data.goal.title}" created!\n\n${data.aiRecommendation}` }]);
    } catch (e: any) { setMsgs(prev => [...prev, { role: 'assistant', content: `❌ ${e.message}` }]); }
    finally { setLoading(false); }
  };

  const generatePath = async () => {
    if (!pathForm.topic) return;
    setPathLoading(true); setStudyPath(null);
    try {
      const res = await fetch(`${API_URL()}/study-buddy/generate-smart-path`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` },
        body: JSON.stringify({ topic: pathForm.topic, currentLevel: pathForm.currentLevel, targetLevel: pathForm.targetLevel, availableHoursPerWeek: pathForm.hoursPerWeek, learningStyle: style, knownTopics: pathForm.knownTopics ? pathForm.knownTopics.split(',').map((t:string)=>t.trim()).filter(Boolean) : [] }),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
      const data = await res.json();
      setStudyPath(data.studyPath);
    } catch (e: any) { alert(`Error: ${e.message}`); }
    finally { setPathLoading(false); }
  };

  const diffColor = (d:string) => ({ beginner:'#34d399', intermediate:'#fbbf24', advanced:'#fb7185' }[d]||'#818cf8');

  return (
    <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}} className="component-container" style={{maxWidth:1100}}>
      <h2>🎯 AI Study Buddy — Nova</h2>
      <p>Your personalised AI learning companion powered by Amazon Bedrock</p>

      {/* Learning Style */}
      <div style={{marginBottom:'1.5rem'}}>
        <div style={{fontSize:'0.78rem',fontWeight:600,color:'var(--text-muted)',textTransform:'uppercase',letterSpacing:'0.07em',marginBottom:'0.6rem'}}>Your Learning Style</div>
        <div style={{display:'flex',gap:'0.6rem',flexWrap:'wrap'}}>
          {[{id:'visual',icon:'👁️'},{id:'auditory',icon:'👂'},{id:'kinesthetic',icon:'✋'},{id:'reading',icon:'📖'}].map(s => (
            <button key={s.id} onClick={()=>setStyle(s.id as any)} style={{padding:'0.5rem 1.1rem',background:style===s.id?'linear-gradient(135deg,var(--indigo),var(--violet-dark))':'rgba(255,255,255,0.04)',border:`1px solid ${style===s.id?'rgba(99,102,241,0.6)':'rgba(255,255,255,0.08)'}`,borderRadius:10,color:style===s.id?'white':'var(--text-secondary)',fontFamily:'var(--font-sans)',fontSize:'0.82rem',fontWeight:600,cursor:'pointer',transition:'all 0.18s'}}>{s.icon} {s.id.charAt(0).toUpperCase()+s.id.slice(1)}</button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{display:'flex',gap:'0.5rem',marginBottom:'1.5rem',borderBottom:'1px solid rgba(255,255,255,0.07)',paddingBottom:'0.5rem'}}>
        {[{id:'chat',label:'💬 Chat & Goals'},{id:'path',label:'🗺️ Smart Study Path'}].map(t=>(
          <button key={t.id} onClick={()=>setTab(t.id as any)} style={{padding:'0.6rem 1.4rem',background:tab===t.id?'linear-gradient(135deg,var(--indigo),var(--secondary))':'transparent',border:`1px solid ${tab===t.id?'var(--indigo)':'rgba(255,255,255,0.08)'}`,borderRadius:'10px 10px 0 0',color:tab===t.id?'white':'var(--text-secondary)',fontFamily:'var(--font-sans)',fontSize:'0.88rem',fontWeight:600,cursor:'pointer',transition:'all 0.18s'}}>{t.label}</button>
        ))}
      </div>

      {insight && <div style={{background:'rgba(139,92,246,0.1)',border:'1px solid rgba(139,92,246,0.3)',borderRadius:12,padding:'0.85rem 1rem',marginBottom:'1.25rem',display:'flex',alignItems:'flex-start',gap:'0.6rem'}}><span style={{fontSize:'1.2rem'}}>💡</span><div><strong style={{color:'var(--violet)',fontSize:'0.8rem'}}>AI Insight</strong><p style={{color:'var(--text-primary)',fontSize:'0.85rem',marginTop:'0.2rem'}}>{insight}</p></div><button onClick={()=>setInsight('')} style={{background:'none',border:'none',color:'var(--text-muted)',cursor:'pointer',marginLeft:'auto',fontSize:'1.1rem'}}>×</button></div>}

      {tab==='chat' && <>
        {/* Goals */}
        <div style={{marginBottom:'1.5rem'}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'0.75rem'}}>
            <div style={{color:'var(--text-secondary)',fontSize:'0.88rem',fontWeight:600}}>🎯 Learning Goals ({goals.length})</div>
            <button onClick={()=>setShowGoalForm(!showGoalForm)} style={{padding:'0.4rem 0.9rem',background:'rgba(99,102,241,0.15)',border:'1px solid rgba(99,102,241,0.35)',borderRadius:8,color:'var(--indigo-light)',fontFamily:'var(--font-sans)',fontSize:'0.8rem',fontWeight:600,cursor:'pointer'}}>+ New Goal</button>
          </div>
          {showGoalForm && <motion.div initial={{height:0,opacity:0}} animate={{height:'auto',opacity:1}} style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:12,padding:'1.25rem',marginBottom:'0.85rem',overflow:'hidden'}}>
            <div style={{display:'grid',gap:'0.75rem'}}>
              <input type="text" placeholder="Goal title (e.g. Master React Hooks)" value={newGoal.title} onChange={e=>setNewGoal({...newGoal,title:e.target.value})} style={{width:'100%',padding:'0.65rem 0.9rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,color:'var(--text-primary)',fontFamily:'var(--font-sans)',fontSize:'0.88rem'}} />
              <textarea placeholder="Description (optional)" value={newGoal.description} onChange={e=>setNewGoal({...newGoal,description:e.target.value})} rows={2} style={{width:'100%',padding:'0.65rem 0.9rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,color:'var(--text-primary)',fontFamily:'var(--font-sans)',fontSize:'0.88rem',resize:'vertical'}} />
              <input type="date" value={newGoal.targetDate} onChange={e=>setNewGoal({...newGoal,targetDate:e.target.value})} style={{padding:'0.65rem 0.9rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,color:'var(--text-primary)',fontFamily:'var(--font-sans)',fontSize:'0.88rem'}} />
              <div style={{display:'flex',gap:'0.6rem'}}>
                <button onClick={createGoal} disabled={loading} style={{flex:1,padding:'0.7rem',background:'linear-gradient(135deg,var(--indigo),var(--violet-dark))',border:'none',borderRadius:8,color:'white',fontFamily:'var(--font-sans)',fontSize:'0.88rem',fontWeight:600,cursor:'pointer',opacity:loading?0.6:1}}>{loading?'Creating…':'✨ Create with AI'}</button>
                <button onClick={()=>setShowGoalForm(false)} style={{padding:'0.7rem 1rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:8,color:'var(--text-secondary)',fontFamily:'var(--font-sans)',cursor:'pointer'}}>Cancel</button>
              </div>
            </div>
          </motion.div>}
          {goals.length > 0 && <div style={{display:'flex',flexDirection:'column',gap:'0.6rem'}}>
            {goals.map(g=><div key={g.id} style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.07)',borderRadius:12,padding:'1rem'}}>
              <div style={{fontWeight:600,color:'var(--text-primary)',marginBottom:'0.3rem'}}>{g.title}</div>
              <div style={{height:4,background:'rgba(255,255,255,0.08)',borderRadius:99,overflow:'hidden',margin:'0.5rem 0'}}><div style={{height:'100%',width:`${g.progress||0}%`,background:'linear-gradient(90deg,var(--indigo),var(--violet))',borderRadius:99}} /></div>
              <div style={{color:'var(--text-muted)',fontSize:'0.75rem'}}>{g.progress||0}% complete</div>
            </div>)}
          </div>}
        </div>

        {/* Chat */}
        <div style={{background:'rgba(0,0,0,0.25)',border:'1px solid rgba(255,255,255,0.07)',borderRadius:14,height:380,overflowY:'auto',padding:'1.25rem',marginBottom:'1rem'}}>
          {msgs.map((m,i)=><div key={i} style={{display:'flex',justifyContent:m.role==='user'?'flex-end':'flex-start',marginBottom:'0.9rem'}}>
            <div style={{maxWidth:'78%',padding:'0.85rem 1.1rem',borderRadius:12,background:m.role==='user'?'linear-gradient(135deg,#6366f1,#4338ca)':'rgba(255,255,255,0.04)',border:m.role==='user'?'none':'1px solid rgba(255,255,255,0.07)',whiteSpace:'pre-wrap',lineHeight:1.65,fontSize:'0.88rem'}}>{m.content}</div>
          </div>)}
          {loading&&<div style={{display:'flex',gap:5,padding:'0.5rem 0'}}>{[0,.2,.4].map((d,i)=><motion.div key={i} animate={{scale:[1,1.4,1]}} transition={{repeat:Infinity,duration:0.7,delay:d}} style={{width:7,height:7,borderRadius:'50%',background:'var(--indigo)'}} />)}</div>}
          <div ref={endRef} />
        </div>
        <div style={{display:'flex',gap:'0.6rem'}}>
          <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()} placeholder="Ask Nova anything about your learning…" style={{flex:1,padding:'0.8rem 1rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:10,color:'var(--text-primary)',fontFamily:'var(--font-sans)',fontSize:'0.88rem',outline:'none'}} />
          <button onClick={send} disabled={loading||!input.trim()} style={{padding:'0.8rem 1.5rem',background:'linear-gradient(135deg,var(--indigo),var(--violet-dark))',border:'none',borderRadius:10,color:'white',fontFamily:'var(--font-sans)',fontWeight:600,cursor:'pointer',opacity:loading||!input.trim()?0.5:1}}>Send</button>
        </div>
      </>}

      {tab==='path' && <>
        {!studyPath ? (
          <div style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:16,padding:'2rem'}}>
            <h3 style={{color:'var(--indigo-light)',marginBottom:'0.4rem',fontSize:'1.1rem'}}>🗺️ AI Smart Study Path Generator</h3>
            <p style={{color:'var(--text-muted)',fontSize:'0.84rem',marginBottom:'1.5rem'}}>Get a personalised roadmap with skill gap analysis, modules, and weekly schedule — powered by Amazon Nova Pro</p>
            <div style={{display:'grid',gap:'1rem'}}>
              <input type="text" placeholder="What do you want to learn? (e.g. Machine Learning, React)" value={pathForm.topic} onChange={e=>setPathForm({...pathForm,topic:e.target.value})} style={{width:'100%',padding:'0.75rem 1rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:10,color:'var(--text-primary)',fontFamily:'var(--font-sans)',fontSize:'0.9rem',outline:'none'}} />
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'1rem'}}>
                {[{l:'Current Level',k:'currentLevel'},{l:'Target Level',k:'targetLevel'}].map(f=><div key={f.k}><div style={{fontSize:'0.78rem',color:'var(--text-muted)',fontWeight:600,textTransform:'uppercase',letterSpacing:'0.06em',marginBottom:'0.4rem'}}>{f.l}</div><select value={(pathForm as any)[f.k]} onChange={e=>setPathForm({...pathForm,[f.k]:e.target.value})} style={{width:'100%',padding:'0.65rem 0.9rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:8,color:'var(--text-primary)',fontFamily:'var(--font-sans)',fontSize:'0.88rem',appearance:'none',cursor:'pointer'}}><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></div>)}
              </div>
              <input type="text" placeholder="Topics you already know (comma-separated, optional)" value={pathForm.knownTopics} onChange={e=>setPathForm({...pathForm,knownTopics:e.target.value})} style={{width:'100%',padding:'0.75rem 1rem',background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.1)',borderRadius:10,color:'var(--text-primary)',fontFamily:'var(--font-sans)',fontSize:'0.88rem',outline:'none'}} />
              <button onClick={generatePath} disabled={pathLoading||!pathForm.topic} style={{padding:'1rem',background:'linear-gradient(135deg,var(--emerald),#059669)',border:'none',borderRadius:10,color:'white',fontFamily:'var(--font-sans)',fontSize:'1rem',fontWeight:700,cursor:pathLoading||!pathForm.topic?'not-allowed':'pointer',opacity:pathLoading||!pathForm.topic?0.55:1}}>
                {pathLoading?'🧠 AI is generating your personalised study path…':'🚀 Generate My Smart Study Path'}
              </button>
            </div>
          </div>
        ) : (
          <motion.div initial={{opacity:0}} animate={{opacity:1}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'1.25rem'}}>
              <h3 style={{color:'var(--indigo-light)',fontSize:'1.1rem',fontWeight:700}}>🗺️ Your Personalised Study Path</h3>
              <button onClick={()=>setStudyPath(null)} className="btn-secondary" style={{padding:'0.45rem 1rem',fontSize:'0.82rem'}}>↺ New Path</button>
            </div>

            {studyPath.skillGapAnalysis && <div style={{background:'rgba(245,158,11,0.07)',border:'1px solid rgba(245,158,11,0.2)',borderRadius:14,padding:'1.25rem',marginBottom:'1.25rem'}}>
              <div style={{color:'#fbbf24',fontWeight:700,marginBottom:'0.85rem',fontSize:'0.92rem'}}>🔍 Skill Gap Analysis</div>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:'1rem'}}>
                {[{l:'✅ Current Skills',sk:'currentSkills',c:'#34d399'},{l:'🎯 Target Skills',sk:'targetSkills',c:'var(--indigo-light)'},{l:'⚠️ Gaps to Fill',sk:'gaps',c:'#fb7185'}].map(s=><div key={s.sk}><div style={{fontWeight:600,color:s.c,fontSize:'0.8rem',marginBottom:'0.4rem'}}>{s.l}</div>{(studyPath.skillGapAnalysis[s.sk]||[]).map((x:string,i:number)=><div key={i} style={{color:'var(--text-secondary)',fontSize:'0.8rem',padding:'0.2rem 0'}}>• {x}</div>)}</div>)}
              </div>
            </div>}

            <div style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.08)',borderRadius:14,padding:'1.25rem',marginBottom:'1.25rem'}}>
              <div style={{color:'var(--indigo-light)',fontWeight:700,marginBottom:'1rem',fontSize:'0.92rem'}}>📚 Learning Modules ({studyPath.modules?.length||0} modules · ~{studyPath.totalEstimatedWeeks} weeks)</div>
              <div style={{position:'relative'}}>
                <div style={{position:'absolute',left:14,top:14,bottom:14,width:2,background:'linear-gradient(180deg,#34d399,#6366f1,#fb7185)',borderRadius:2}} />
                {studyPath.modules?.map((mod: any,i: number)=>(
                  <div key={i} style={{display:'flex',gap:'1rem',marginBottom:'0.85rem',paddingLeft:44,position:'relative'}} onClick={()=>setExpandedMod(expandedMod===i?null:i)}>
                    <div style={{position:'absolute',left:6,top:'50%',transform:'translateY(-50%)',width:20,height:20,borderRadius:'50%',background:diffColor(mod.difficulty),display:'flex',alignItems:'center',justifyContent:'center',color:'white',fontWeight:700,fontSize:'0.75rem',zIndex:1}}>{i+1}</div>
                    <div style={{flex:1,background:expandedMod===i?'rgba(99,102,241,0.1)':'rgba(255,255,255,0.02)',border:`1px solid ${expandedMod===i?'rgba(99,102,241,0.4)':'rgba(255,255,255,0.07)'}`,borderRadius:10,padding:'0.85rem',cursor:'pointer',transition:'all 0.18s'}}>
                      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                        <div style={{flex:1}}>
                          <div style={{display:'flex',alignItems:'center',gap:'0.5rem',marginBottom:'0.2rem'}}>
                            <span style={{fontWeight:600,color:'var(--text-primary)',fontSize:'0.9rem'}}>{mod.title}</span>
                            <span style={{background:diffColor(mod.difficulty),color:'white',padding:'0.1rem 0.45rem',borderRadius:4,fontSize:'0.68rem',fontWeight:700}}>{mod.difficulty}</span>
                          </div>
                          <p style={{color:'var(--text-muted)',fontSize:'0.8rem'}}>{mod.description}</p>
                        </div>
                        <span style={{color:'var(--text-muted)',fontSize:'0.78rem',marginLeft:'1rem',whiteSpace:'nowrap'}}>⏱ {mod.estimatedHours}h</span>
                      </div>
                      {expandedMod===i&&<div style={{marginTop:'0.85rem',paddingTop:'0.85rem',borderTop:'1px solid rgba(255,255,255,0.07)'}}>
                        {mod.learningObjectives?.length>0&&<div style={{marginBottom:'0.6rem'}}><div style={{color:'#34d399',fontSize:'0.75rem',fontWeight:700,textTransform:'uppercase',marginBottom:'0.3rem'}}>Learning Objectives</div>{mod.learningObjectives.map((o:string,j:number)=><div key={j} style={{color:'var(--text-secondary)',fontSize:'0.8rem',padding:'0.15rem 0'}}>• {o}</div>)}</div>}
                        {mod.resources?.length>0&&<div><div style={{color:'#fbbf24',fontSize:'0.75rem',fontWeight:700,textTransform:'uppercase',marginBottom:'0.3rem'}}>Resources</div>{mod.resources.map((r:any,j:number)=><div key={j} style={{color:'var(--text-secondary)',fontSize:'0.78rem',padding:'0.15rem 0'}}>[{r.type}] <strong>{r.title}</strong> — {r.description}</div>)}</div>}
                      </div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {studyPath.motivationalTip&&<div style={{background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.25)',borderRadius:12,padding:'1rem',display:'flex',gap:'0.75rem',alignItems:'flex-start'}}>
              <span style={{fontSize:'1.5rem'}}>💪</span><p style={{color:'var(--text-primary)',fontSize:'0.88rem',lineHeight:1.65}}>{studyPath.motivationalTip}</p>
            </div>}
          </motion.div>
        )}
      </>}
    </motion.div>
  );
};
export default AIStudyBuddy;
