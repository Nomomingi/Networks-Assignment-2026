# Project documentation

## Overview
This project is a TCP chat application with:

- A **terminal client** (`Client.py`)
- A **TCP server** (`Server.py`)
- A **MySQL persistence layer** (`db.py`)
- **Peer-to-peer file transfer** via ngrok + direct TCP (`p2p.py`)

The server is used for messaging, persistence, and *signaling* for file transfer.
File bytes do **not** pass through the server.

## Text packet framing (TCP)
Both client and server speak a simple line-based protocol over TCP.

- A packet is **multiple lines** separated by `\n`.
- A packet ends with a **blank line** (`\n\n`).
- The **first line** is the action name (e.g. `LOGIN`, `PRIVATE`, `GROUP_MESSAGE`).

In code, both sides typically implement:

- `receive_packet(...)`: read until `\n\n` is encountered, then split into lines.
- `send_message(...)`: send a UTF-8 string over TCP.

## Protocol action mapping (`Protocol.py`)
The `Protocol` enum is the single source of truth for action IDs.

- `Protocol.initiate_protocol(num)` converts a numeric ID back to an action string.
- Client and server must use the same mapping.

Current enum values:

- `LOGIN = 1`
- `CREATE = 2`
- `CLOSE = 3`
- `PRIVATE = 4`
- `SEARCH = 5`
- `CONTACTS = 6`
- `PING = 7` (UDP)
- `OPEN_CHAT = 8`
- `CLOSE_CHAT = 9`
- `SEND_BLOB = 10`
- `RECIEVE_BLOB = 11`
- `GROUP_CREATE = 12`
- `GROUP_LIST = 13`
- `GROUP_OPEN = 14`
- `GROUP_MESSAGE = 15`
- `GROUP_CLOSE = 16`
- `GROUP_ADD_MEMBER = 17`
- `GROUP_SEND_BLOB = 18`

## Request/response formats
### Account
#### LOGIN
Client -> Server:

```
LOGIN
<username>
<password>

```

Server -> Client:

- `OK|LOGIN_SUCCESS` or an `ERROR|...`

#### CREATE
Client -> Server:

```
CREATE
<username>
<password>

```

Server -> Client:

- `OK|SIGNUP_SUCCESSFUL` or an `ERROR|...`

### Search
Client -> Server:

```
SEARCH
<query>

```

Server -> Client:

```
OK|SEARCH
<username>
<username>
...

```

### Contacts
Client -> Server:

```
CONTACTS

```

Server -> Client:

```
OK|CONTACTS
<username>|ONLINE
<username>|OFFLINE
...

```

### Private chat
#### Open chat history
Client -> Server:

```
OPEN_CHAT
<peer_username>

```

Server -> Client:

```
OK|CHAT_HISTORY
<sender>|<message_text>|<timestamp>
...

```

#### Send message
Client -> Server:

```
PRIVATE
<peer_username>
<message_text>

```

Server -> Client (sender):

- `OK|MESSAGE_SENT` (if pushed immediately)
- `OK|PRIVATE_STORED` (if stored only)

Server -> Client (receiver, realtime push only):

```
INCOMING_PRIVATE
<sender_username>
<message_text>

```

#### Close chat
Client -> Server:

```
CLOSE_CHAT
<peer_username>

```

Server -> Client:

- `OK|CHAT_CLOSED`

### Group chat
#### Create group
Client -> Server:

```
GROUP_CREATE
<group_name>
<member_username>
<member_username>
...

```

Server -> Client:

- `OK|GROUP_CREATED|<group_id>` or an `ERROR|...`

#### List groups
Client -> Server:

```
GROUP_LIST

```

Server -> Client:

```
OK|GROUPS
<group_id>|<group_name>
...

```

#### Open group history
Client -> Server:

```
GROUP_OPEN
<group_id>

```

Server -> Client:

```
OK|GROUP_HISTORY
<sender>|<message_text>|<timestamp>
...

```

#### Send group message
Client -> Server:

```
GROUP_MESSAGE
<group_id>
<message_text>

```

Server -> Client (sender):

- `OK|GROUP_MESSAGE_SENT`

Server -> Client (receiver, realtime push only):

```
INCOMING_GROUP
<group_id>
<sender_username>
<message_text>

```

#### Add member
Client -> Server:

```
GROUP_ADD_MEMBER
<group_id>
<new_member_username>

```

Server -> Client:

- `OK|MEMBER_ADDED` or an `ERROR|...`

#### Close group
Client -> Server:

```
GROUP_CLOSE
<group_id>

```

Server -> Client:

- `OK|GROUP_CLOSED`

## UDP ping protocol
Used to track online status.

Client -> Server (UDP):

- `PING|<username>` every `PING_TIME` seconds

Server behavior:

- Records last-seen times in `users_last_seen`
- A background thread removes stale users from `online_users`

## Peer-to-peer file transfer (`p2p.py`)
File transfer is done directly between clients.

### Signaling
The sender creates an ngrok TCP tunnel to a local TCP listener, then informs the server.

Sender -> Server:

```
SEND_BLOB
<sender_username>
<peer_username>
<filename>
<ngrok_host>
<ngrok_port>

```

Server -> Receiver:

```
BLOB_OFFER
<sender_username>
<ngrok_host>
<ngrok_port>
<filename>

```

Group signaling is similar:

Sender -> Server:

```
GROUP_SEND_BLOB
<group_id>
<filename>
<ngrok_host>
<ngrok_port>

```

Server -> Receivers:

```
GROUP_BLOB_OFFER
<group_id>
<sender_username>
<ngrok_host>
<ngrok_port>
<filename>

```

### Direct transfer wire format
On the direct P2P TCP connection, the sender streams framed chunks:

- `[4-byte big-endian length][payload]` repeated
- `[4-byte length = 0]` indicates EOF

### Save location
Received files are saved under:

- `<OS Downloads folder>/group81/`

The OS Downloads folder is resolved at runtime (Windows/macOS/Linux).

## File-by-file responsibilities
### `Client.py`
- Main terminal UI and state machine
- Sends requests to the server via `send_message()`
- Uses `receive_packet()` in background threads during chat
- Calls `p2p.send_blob()` / `p2p.send_group_blob()` for file sending
- Calls `p2p.receive_blob()` when receiving `BLOB_OFFER` / `GROUP_BLOB_OFFER`

### `Server.py`
- Accepts TCP clients and dispatches actions
- Tracks:
  - `online_users`: who is connected
  - `active_chats`: who is currently viewing which private chat
  - `active_groups`: who is currently inside which group
- Stores all messages in MySQL via `db.py`
- Sends realtime pushes only when the receiver is currently in the relevant chat

### `db.py`
- All MySQL persistence
- Users, private messages, groups, group messages, membership

### `Protocol.py`
- Enum mapping for action names/IDs

### `ClientStates.py`
- Client state enum used by `Client.py`

### `p2p.py`
- ngrok tunnel creation
- direct TCP streaming (chunk framing)
- saving received files into OS Downloads
