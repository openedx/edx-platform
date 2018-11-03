#include <stdio.h>
#include <sys/un.h>
#include <string.h>

#include <zmq.h>
#include "zmq_compat.h"

int get_ipc_path_max_len(void) {
    struct sockaddr_un *dummy;
    return sizeof(dummy->sun_path) - 1;
}
