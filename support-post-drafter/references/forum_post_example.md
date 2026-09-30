# Reference forum post: "Problem with socket configuration while using MXCHIP Wi-Fi Component"

> Real-world example of a successful ST Community forum post. Note the structure:
> context first, precise symptom, numbered repro steps, minimal code, environment/workaround
> notes, motivation, and an explicit open-ended question.

---

## Metadata (as posted)
- Title: Problem with socket configuration while using MXCHIP Wi-Fi Component
- Replies: 0 | Views: 41
- Board: B-U585I-IOT02A (STM32U585AI)
- Wi-Fi component: EMW3080 / MXCHIP, driver repo: https://github.com/STMicroelectronics/stm32-mx-wifi/tree/main

## Post body

Hi,

I have been developing IoT application for the B-U585I-IOT02A (STM32U585AI) and encountered following problem:

When attempting to set a socket to non-blocking mode `MX_SO_BLOCKMODE = 1` using the `MX_WIFI_Socket_setsockopt()` API the call fails immediately and returns -1.

### Steps to reproduce:
1. Create a socket using `MX_WIFI_Socket_create()`
2. Try to configure `MX_SO_BLOCKMODE = 1` via `MX_WIFI_Socket_setsockopt()`
3. Get instant -1 in the runtime

### Minimal Reproducible Code

```c
#include "mx_wifi.h"
#include "mx_wifi_bare_os.h" /* Using Bare OS mode */

void test_nonblocking_socket_config(void)
{
    int32_t sock = -1;
    int32_t optval = 1; /* 1 = Non-blocking mode */
    int32_t ret = -1;

    /* 1. Create TCP Socket */
    sock = MX_WIFI_Socket_create(MX_WIFI_AF_INET,
                                 MX_WIFI_SOCK_STREAM,
                                 MX_WIFI_IPPROTO_TCP);
    if (sock < 0)
    {
        /* Handle socket creation failure */
        return;
    }

    /* 2. Configure Socket to Non-blocking Mode */
    ret = MX_WIFI_Socket_setsockopt(sock,
                                    MX_WIFI_SOL_SOCKET,
                                    MX_SO_BLOCKMODE,
                                    &optval,
                                    sizeof(optval));
    /* FAILS HERE: ret returns -1 immediately at runtime */
    if (ret < 0)
    {
        /* Socket option rejected by driver/module */
    }
}
```

The Wi-Fi link is verified and connected prior to running this code. I am currently using the Bare OS abstraction (`mx_wifi_bare_os.h`) because CMSIS-RTOS v2 integration (`mx_wifi_cmsis_os.h`) encountered separate compatibility issues with this setup.

While I am currently working around this issue using standard blocking sockets, non-blocking socket I/O is highly recommended when integrating with the coreMQTT agent library to allow background command loop processing and avoid task starvation.

Has anyone encountered this restriction with `MX_SO_BLOCKMODE` on the EMW3080 component, or is there an alternative mechanism to achieve non-blocking reads/writes with the stm32 mx wi-fi driver?

WI-FI component: https://github.com/STMicroelectronics/stm32-mx-wifi/tree/main
