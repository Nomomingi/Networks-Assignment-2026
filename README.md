This is our group's prototype of a instant messaging application, fully designed in python.


### **How to run the db**
1. Make sure you have mysql set up on your machine.
2. Run `make db` to initialise the schema.
3. Verify the tables were created by checking mysql workbench or via your terminal.
4. Populate the db with dummy data with the following command: `make seed`.


### **DB Python Setup**
1. Install the dependencies using the following command:
    ```bash
    make requirements
    ```
    **Note:** Make sure to be running a **unix based terminal** in order to be able to use make commands. Otherwise, you can watch a YouTube tutorial on the Windows set. 
2. Create a `.env` file to store environment variables using the following command:
```bash
make env
```
- The environment variables ensure that our secret info such as passwwords, api keys, etc are not accessible to the public or pushed to github.
- The `make env` command will not fill in your mysql password, so you should add that manually in the `.env` file. Also just verify that the `DB_USER` and `HOST` variables match your mysql host and user - the one you made during the mysql setup in CSC2001F or whenever you set it up.

3. Test that the db connection works by running the `db.py` file. If you ran the `seed.sql` file initially, you should see something like:
```bash
➜  nets git:(db-methods) ✗ python3 db.py
DB connection successful [(1, 'paul', 'pass123', 1, datetime.datetime(2026, 3, 2, 19, 17, 10)), (2, 'paulihno', '123pass', 1, datetime.datetime(2026, 3, 2, 19, 17, 10))]
➜  nets git:(db-methods) ✗ 
```