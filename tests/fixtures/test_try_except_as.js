function func() {
    try {
        do_something();
    } catch (__dummy0__) {
        if (__dummy0__ instanceof Error) {
            var e = __dummy0__;
            handle_error(e);
        } else {
            throw __dummy0__;
        }
    }
}
