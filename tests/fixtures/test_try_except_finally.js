function func() {
    try {
        do_something();
    } catch (__dummy0__) {
        if (__dummy0__ instanceof Error) {
            handle_error();
        } else {
            throw __dummy0__;
        }
    } finally {
        cleanup();
    }
}
