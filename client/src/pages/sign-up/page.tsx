import { useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuth } from '@/context/auth-context';
import styles from './index.module.css';

export default function SignUp() {
    const { signup } = useAuth();
    const navigate = useNavigate();

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);
        const err = await signup(username, password);
        setLoading(false);
        if (err) {
            setError(err);
        } else {
            navigate('/');
        }
    };

    return (
        <>
            <div className={styles.container}>
                <div className={styles.header}>Sign Up</div>
                <div className={styles.subtitle}>&gt;&gt; create an account &lt;&lt;</div>
                <form className={styles.col} onSubmit={handleSubmit}>
                    <input
                        className={styles.input}
                        type="text"
                        placeholder="Username"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        required
                    />
                    <input
                        className={styles.input}
                        type="password"
                        placeholder="Password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        required
                    />
                    {error && <p className={styles.error}>{error}</p>}
                    <button className={styles.button} type="submit" disabled={loading}>
                        {loading ? 'Creating account…' : 'Sign Up'}
                    </button>
                </form>
                <p className={styles.footer}>
                    Already have an account? <Link to="/login">Log In</Link>
                </p>
            </div>
        </>
    );
}