#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <assert.h>

char SERVER_RESPONSE[4000], REQUEST[2000];

// Function to build an HTTP GET REQUEST
void build_get_request(const char *host, const char *session_id)
{
    sprintf(REQUEST,
            "GET /api/messages HTTP/1.1\r\n"
            "Host: %s\r\n"
            "Connection: close\r\n"
            "Cookie: session_id=%s\r\n"
            "\r\n",
            host, session_id);
}

// Function to build an HTTP POST REQUEST with a message
void build_post_request(const char *host, const char *session_id, const char *message)
{
    char message_body[1024];
    sprintf(message_body, "{\"msg\": \"%s\"}", message);

    sprintf(REQUEST,
            "POST /api/messages HTTP/1.1\r\n"
            "Host: %s\r\n"
            "Connection: close\r\n"
            "Content-Type: application/x-www-form-urlencoded\r\n"
            "Content-Length: %lu\r\n"
            "Cookie: session_id=%s\r\n"
            "\r\n"
            "%s",
            host, strlen(message_body), session_id, message_body);
}

int build_sockaddr(struct sockaddr **server_addr, const char *host, const int port)
{
    struct addrinfo hints, *res;
    struct sockaddr_in *server_addr_in = malloc(sizeof(struct sockaddr_in));
    if (server_addr_in == NULL)
    {
        perror("Memory allocation failed");
        return -1;
    }

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET; // Specify IPv4
    hints.ai_socktype = SOCK_STREAM;

    int status = getaddrinfo(host, NULL, &hints, &res);
    if (status != 0)
    {
        fprintf(stderr, "getaddrinfo error: %s\n", gai_strerror(status));
        free(server_addr_in);
        return -1;
    }

    // Configure server address
    server_addr_in->sin_family = AF_INET;
    server_addr_in->sin_port = htons(port);
    server_addr_in->sin_addr = ((struct sockaddr_in *)res->ai_addr)->sin_addr;
    freeaddrinfo(res);

    *server_addr = (struct sockaddr *)server_addr_in; // Assign to the caller's pointer
    return 0;
}

int post_msg_test(const struct sockaddr *server_addr, const char *host, const char *message)
{
    const char *session_id = "test-id";
    int socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    char *expected_response = NULL;
    if (socket_desc < 0)
    {
        printf("Unable to create socket\n");
        return -1;
    }
    printf("Socket created successfully\n");

    // Connect to server
    if (connect(socket_desc, server_addr, sizeof(struct sockaddr_in)) < 0)
    {
        printf("Unable to connect\n");
        close(socket_desc);
        return -1;
    }
    printf("Connected to server successfully\n");

    // First, send a GET REQUEST to check existing messages
    build_get_request(host, session_id);
    if (send(socket_desc, REQUEST, strlen(REQUEST), 0) < 0)
    {
        printf("Unable to send GET REQUEST\n");
        close(socket_desc);
        return -1;
    }
    printf("GET REQUEST sent to retrieve messages\n");

    // Receive server response
    memset(SERVER_RESPONSE, '\0', sizeof(SERVER_RESPONSE));
    if (recv(socket_desc, SERVER_RESPONSE, sizeof(SERVER_RESPONSE), 0) < 0)
    {
        printf("Error receiving response\n");
        close(socket_desc);
        return -1;
    }

    expected_response = "HTTP/1.1 200 OK";
    assert(strstr(SERVER_RESPONSE, expected_response) != NULL);
    printf("Server response to GET:\n%s\n", SERVER_RESPONSE);

    // Close and reopen socket to send POST REQUEST
    close(socket_desc);
    socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    if (connect(socket_desc, server_addr, sizeof(struct sockaddr_in)) < 0)
    {
        printf("Unable to reconnect\n");
        close(socket_desc);
        return -1;
    }

    // Send POST REQUEST with the message
    build_post_request(host, session_id, message);
    if (send(socket_desc, REQUEST, strlen(REQUEST), 0) < 0)
    {
        printf("Unable to send POST REQUEST\n");
        close(socket_desc);
        return -1;
    }

    printf("\nPOST REQUEST sent with message: %s\n", message);

    // Receive server response for POST
    memset(SERVER_RESPONSE, '\0', sizeof(SERVER_RESPONSE));
    if (recv(socket_desc, SERVER_RESPONSE, sizeof(SERVER_RESPONSE), 0) < 0)
    {
        printf("Error receiving response to POST\n");
        close(socket_desc);
        return -1;
    }
    
    expected_response = "HTTP/1.1 201 Created";
    assert(strstr(SERVER_RESPONSE, expected_response) != NULL);

    close(socket_desc);
    socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    if (connect(socket_desc, server_addr, sizeof(struct sockaddr_in)) < 0)
    {
        printf("Unable to reconnect\n");
        close(socket_desc);
        return -1;
    }

    build_get_request(host, session_id);
    if (send(socket_desc, REQUEST, strlen(REQUEST), 0) < 0)
    {
        printf("Unable to send GET REQUEST\n");
        close(socket_desc);
        return -1;
    }

    memset(SERVER_RESPONSE, '\0', sizeof(SERVER_RESPONSE));
    if (recv(socket_desc, SERVER_RESPONSE, sizeof(SERVER_RESPONSE), 0) < 0)
    {
        printf("Error receiving response to POST\n");
        close(socket_desc);
        return -1;
    }

    assert(strstr(SERVER_RESPONSE, message) != NULL);
    printf("\nServer response to GET:\n%s\n", SERVER_RESPONSE);
    // Verify if the message was successfully posted
    if (strstr(SERVER_RESPONSE, message) != NULL)
    {
        printf("\nMessage successfully posted and verified.\n\n\033[0;32mTest 1 passed\033[0m\n\n");
    }
    else
    {
        printf("Message not found in server response.\n\n[0;31mTest 1 Failed\033[0m\n");
    }

    // Close the socket
    close(socket_desc);

    return 0;
}

// Attempt to get post as user that is not logged in.
int get_msg_test_without_login(const struct sockaddr *server_addr, const char *host, const char *session_id)
{
    // const char *session_id = "not-test-id";
    int socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    if (socket_desc < 0)
    {
        printf("Unable to create socket\n");
        return -1;
    }
    printf("Socket created successfully\n");

    // Connect to server
    if (connect(socket_desc, server_addr, sizeof(struct sockaddr_in)) < 0)
    {
        printf("Unable to connect\n");
        close(socket_desc);
        return -1;
    }
    printf("Connected to server successfully\n");

    // First, send a GET REQUEST to check existing messages
    build_get_request(host, session_id);
    if (send(socket_desc, REQUEST, strlen(REQUEST), 0) < 0)
    {
        printf("Unable to send GET REQUEST\n");
        close(socket_desc);
        return -1;
    }
    printf("GET REQUEST sent to retrieve messages\n");

    // Receive server response
    memset(SERVER_RESPONSE, '\0', sizeof(SERVER_RESPONSE));
    if (recv(socket_desc, SERVER_RESPONSE, sizeof(SERVER_RESPONSE), 0) < 0)
    {
        printf("Error receiving response\n");
        close(socket_desc);
        return -1;
    }
    printf("Server response to GET:\n%s\n", SERVER_RESPONSE);

    //If 401 error is returned then the test passes
    const char *expected_response = "HTTP/1.1 401";
    assert(strstr(SERVER_RESPONSE, expected_response) != NULL);

    if(strstr(SERVER_RESPONSE, expected_response) != NULL){
        printf("\nCorrect Error response is provided for not logged in user.\n\n\033[0;32mTest 2 Passed\033[0m\n");
    } else {
        printf("\nIncorrect or no Error response is provided for not logged in user.\n\n\033[0;31mTest 2 Failed\033[0m\n");
    }
    close(socket_desc);

    return 0;
}

int main(int argc, char *argv[])
{
    if (argc != 5)
    {
        fprintf(stderr, "Usage: %s <host> <port> <session_id> <message>\n", argv[0]);
        return 1;
    }

    const char *host = argv[1];
    int port = atoi(argv[2]);
    const char *session_id = argv[3];
    const char *message = argv[4];

    struct sockaddr *server_addr = NULL;
    if (build_sockaddr(&server_addr, host, port) == -1)
    {
        printf("\nError while making sockaddr\n");
        return -1;
    }

    if (post_msg_test(server_addr, host, message) == -1)
    {
        printf("\nError occurred while running Test 1, stopping the Test 1\n");
    }

    if (get_msg_test_without_login(server_addr, host, session_id) == -1)
    {
        printf("\nError occurred while running Test, stopping the Test 2\n");
    }

    free(server_addr); // Free the allocated memory for sockaddr
    return 0;
}
