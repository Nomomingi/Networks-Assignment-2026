import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/context/auth-context';
import styles from './index.module.css';

const API = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

// ─── Types ────────────────────────────────────────────────────────

interface ChatMessage {
    sender: string;
    text: string;
    ts: string;
}

// ─── Component ────────────────────────────────────────────────────

const Home = () => {
    const { user, logout } = useAuth();

    const [contacts, setContacts] = useState<string[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<string[]>([]);
    const [showSearch, setShowSearch] = useState(false);
    const [activePeer, setActivePeer] = useState<string | null>(null);
    const [history, setHistory] = useState<ChatMessage[]>([]);
    const [inputText, setInputText] = useState('');
    const [loadingChat, setLoadingChat] = useState(false);

    const messagesRef = useRef<HTMLDivElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    // ── Load contacts on mount ──────────────────────────────────────
    useEffect(() => {
        if (!user) return;
        fetch(`${API}/api/contacts?user=${encodeURIComponent(user)}`)
            .then(r => r.json())
            .then(d => setContacts(d.contacts ?? []))
            .catch(() => { });
    }, [user]);

    // ── WebSocket for real-time incoming messages ───────────────────
    useEffect(() => {
        if (!user) return;

        const ws = new WebSocket(`${WS_URL}?user=${encodeURIComponent(user)}`);
        wsRef.current = ws;

        ws.onmessage = (ev) => {
            try {
                const msg = JSON.parse(ev.data);
                if (msg.type === 'message') {
                    const newMsg: ChatMessage = {
                        sender: msg.from,
                        text: msg.text,
                        ts: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
                    };
                    setHistory(prev => {
                        // Only show if we're in that chat (or always show & let user notice)
                        return [...prev, newMsg];
                    });
                    // Add to contacts if not already there
                    setContacts(prev =>
                        prev.includes(msg.from) ? prev : [msg.from, ...prev]
                    );
                }
            } catch { /* ignore */ }
        };

        return () => { ws.close(); wsRef.current = null; };
    }, [user]);

    // ── Auto-scroll to latest message ──────────────────────────────
    useEffect(() => {
        if (messagesRef.current) {
            messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
        }
    }, [history]);

    // ── Debounced search ───────────────────────────────────────────
    useEffect(() => {
        if (searchTimer.current) clearTimeout(searchTimer.current);
        if (!searchQuery.trim()) { setSearchResults([]); setShowSearch(false); return; }

        searchTimer.current = setTimeout(async () => {
            try {
                const r = await fetch(
                    `${API}/api/search?user=${encodeURIComponent(user!)}&q=${encodeURIComponent(searchQuery)}`
                );
                const d = await r.json();
                setSearchResults(d.results ?? []);
                setShowSearch(true);
            } catch { /* ignore */ }
        }, 300);

        return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
    }, [searchQuery, user]);

    // ── Open a chat ─────────────────────────────────────────────────
    const openChat = useCallback(async (peer: string) => {
        if (!user) return;
        setSearchQuery('');
        setShowSearch(false);
        setLoadingChat(true);
        setActivePeer(peer);
        setHistory([]);

        try {
            const r = await fetch(`${API}/api/open-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user, peer }),
            });
            const d = await r.json();
            setHistory(d.history ?? []);
            // Ensure peer appears in contacts sidebar
            setContacts(prev =>
                prev.includes(peer) ? prev : [...prev, peer]
            );
        } catch { /* ignore */ } finally {
            setLoadingChat(false);
        }
    }, [user]);

    // ── Close chat when switching away ─────────────────────────────
    const closeCurrentChat = useCallback(async (peer: string) => {
        if (!user || !peer) return;
        await fetch(`${API}/api/close-chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user, peer }),
        }).catch(() => { });
    }, [user]);

    const handleSelectContact = async (peer: string) => {
        if (activePeer && activePeer !== peer) await closeCurrentChat(activePeer);
        await openChat(peer);
    };

    // ── Send a message ─────────────────────────────────────────────
    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputText.trim() || !activePeer || !user) return;

        const text = inputText.trim();
        setInputText('');

        // Optimistic update
        setHistory(prev => [...prev, {
            sender: user,
            text,
            ts: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
        }]);

        try {
            await fetch(`${API}/api/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user, peer: activePeer, text }),
            });
        } catch { /* ignore */ }
    };

    // ── Logout ─────────────────────────────────────────────────────
    const handleLogout = async () => {
        if (activePeer) await closeCurrentChat(activePeer);
        await fetch(`${API}/api/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user }),
        }).catch(() => { });
        logout();
    };

    // ─────────────────────────────────────────────────────────────
    return (
        <div className={styles.shell}>

            {/* Title bar */}
            <div className={styles.titleBar}>
                <div className={styles.titleBarLeft}>
                    <span className={styles.logo}>GREWP 81</span>
                    <span className={styles.version}>v1.0 // 2026</span>
                </div>
                <div className={styles.titleBarRight}>
                    <span className={styles.userChip}>[ {user} ]</span>
                    <button className={styles.logoutBtn} onClick={handleLogout}>
                        exit
                    </button>
                </div>
            </div>

            {/* Main two-panel layout */}
            <div className={styles.main}>

                {/* Sidebar */}
                <aside className={styles.sidebar}>
                    {/* Search */}
                    <div className={styles.searchBox}>
                        <input
                            className={styles.searchInput}
                            type="text"
                            placeholder="&gt; search users..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            onBlur={() => setTimeout(() => setShowSearch(false), 150)}
                            onFocus={() => searchResults.length && setShowSearch(true)}
                        />
                        {showSearch && searchResults.length > 0 && (
                            <div className={styles.searchResults}>
                                {searchResults.map(u => (
                                    <div
                                        key={u}
                                        className={styles.searchResultItem}
                                        onMouseDown={() => handleSelectContact(u)}
                                    >
                                        &gt; {u}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Contacts list */}
                    <div className={styles.contactsLabel}>contacts</div>
                    <div className={styles.contactsList}>
                        {contacts.length === 0
                            ? <div className={styles.noContacts}>no contacts yet</div>
                            : contacts.map(c => (
                                <div
                                    key={c}
                                    className={`${styles.contactItem} ${activePeer === c ? styles.active : ''}`}
                                    onClick={() => handleSelectContact(c)}
                                >
                                    <span className={styles.onlineDot} />
                                    {c}
                                </div>
                            ))
                        }
                    </div>

                    {/* New Group */}
                    <div className={styles.sidebarBottom}>
                        <button className={styles.newGroupBtn}>
                            + new group
                        </button>
                    </div>
                </aside>

                {/* Chat panel */}
                <section className={styles.chatPanel}>
                    {!activePeer ? (
                        <div className={styles.chatEmpty}>
                            &gt;&gt; select a contact or search<br />
                            to start chatting &lt;&lt;
                        </div>
                    ) : (
                        <>
                            {/* Chat header */}
                            <div className={styles.chatHeader}>
                                chatting with: <span className={styles.chatHeaderName}>{activePeer}</span>
                            </div>

                            {/* Messages */}
                            <div className={styles.messages} ref={messagesRef}>
                                {loadingChat && (
                                    <div className={styles.loadingMsg}>loading history...</div>
                                )}
                                {history.map((m, i) => (
                                    <div key={i} className={styles.msgRow}>
                                        <span className={styles.msgTs}>[{m.ts}]</span>
                                        <span className={`${styles.msgSender} ${m.sender === user ? styles.mine : styles.theirs}`}>
                                            {m.sender}:
                                        </span>
                                        <span className={styles.msgText}>{m.text}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Input */}
                            <form className={styles.inputBar} onSubmit={sendMessage}>
                                <input
                                    type="text"
                                    placeholder="> type a message..."
                                    value={inputText}
                                    onChange={e => setInputText(e.target.value)}
                                    autoFocus
                                />
                                <button
                                    className={styles.sendBtn}
                                    type="submit"
                                    disabled={!inputText.trim()}
                                >
                                    send
                                </button>
                            </form>
                        </>
                    )}
                </section>
            </div>
        </div>
    );
};

export default Home;