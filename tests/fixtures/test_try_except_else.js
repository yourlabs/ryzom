function func() {
    var __dummy0__ = true;
    try {
        do_something();
    } catch (__dummy1__) {
        __dummy0__ = false;
        if (__dummy1__ instanceof Error) {
            handle_error();
        } else {
            throw __dummy1__;
        }
    } finally {
        if (__dummy0__) {
            on_success();
        }
    }
}
