## Part 1

### Files
- **chat_server.py**: Backend server that manages the chat, with some modification so that it can handle *web clients* and *terminal clients* seprately.
- **web_server.py**: Multi-threared Server that will talk to the *chat_server* and will handle the request of *web clients* respectively.
- **chatbot.db**: SQLite3 database for storing chat data.
- **website**: A folder containing necessary files for the frontend web page.
  
### How to run
1. **chat_server.py**:
   - Command: python3 chat_server.py
   - Description: This will start the chat server that will listen ternimal clients on port `8640` and web clients on port `8641`.
2. **web_server.py**:
   - Command: python3 web_server.py
   - Description: This will the web server that will listen for the web clients *HTTP* request on port `8642`.
  
## Part 2

### Files

- **web_server_2.py**: Web server for testing purpose. This is same as **web_server** in part1, the only difference is it has `"test-id"` stored as a valid *session_id* in it's cache memory (CACHE_DIR), and it runs on different port
- **chat_sever.py**: Exact same as chat_server.py in part1. Don't know why it is here, LOL!
- **server_test.c**: C file to run 2 test on server.
- **Makefile**: Makefile to compile the *sever_test.c* file
- **chatbot.db**: SQLite3 database for storing chat data.

### How to Run

1. **web_server_2.py**: python3 web_server_2.py. This server is listining client for testing on port `8643`.
2. **chat_server.py**: python3 chat_server.py
3. **server_test.c**: 
   - Command: First run `make` command to create `a2` executable file for *server_test.c* file. Then run the `a2` file with command 
   - `./a2 server_name server_port session_id message`.
   - Note: In assignment description it is mentioned to take *username* as argument, but I am using *session_id* to manage multiple clients, that's why I decided to take *session_id* in arguments. Also, provide a invalid *session_id* so that I use that for `Test 2` that related to logged out user, you can provide any random letter other than `"test-id"` and it will work. You can use the following command as example to run `a2`
   - `./a2 eagle.cs.umanitoba.ca 8643 hkf-fhui randomMessage6873`

### Note
- Run both web_server.py and chat_server.py before connecting with chrome
- Run both web_server_2.py and chat_server.py before running the c test file.
- I have written my code **a2** such that it will run on `eagle.cs.umanitoba.ca`, so please run the code on `eagle.cs.umanitoba.ca` or else it might not work.
