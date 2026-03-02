INSERT INTO Users (username, user_password, logged_in) VALUES
('paul', 'pass123', TRUE),
('paulihno', '123pass', TRUE);

INSERT INTO PrivateMessages (sender_id, receiver_id, message_text) VALUES
(1, 2, 'Hello Werld!'),
(2, 1, 'Howzit big bro?');

INSERT INTO GroupChat (group_name, created_by) VALUES
('TEst', 1);

INSERT INTO GroupChatMembers (group_id, user_id) VALUES
(1, 1),
(1, 2);

INSERT INTO GroupMessages (group_id, sender_id, message_text) VALUES
(1, 1, 'Welkom to the group'),
(1, 2, 'Thank you for addding me');