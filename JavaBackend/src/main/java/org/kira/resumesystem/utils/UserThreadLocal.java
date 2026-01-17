package org.kira.resumesystem.utils;

public class UserThreadLocal {
    private static final ThreadLocal<Long> userIdThreadLocal = new ThreadLocal<>();

    public static void set(Long userId) {
        userIdThreadLocal.set(userId);
    }

    public static Long get() {
        return userIdThreadLocal.get();
    }

    public static void remove() {
        userIdThreadLocal.remove();
    }
}
