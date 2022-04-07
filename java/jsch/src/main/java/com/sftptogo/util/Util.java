package com.sftptogo.util;

import java.text.StringCharacterIterator;

public class Util {
    private Util() {
        throw new IllegalArgumentException("Not instantiable");
    }

    /**
     * File size in bytes
     *
     * @param bytes size of file
     * @return human-readable file size using binary unit
     */
    public static String humanReadableByteCount(long bytes) {
        long absB = bytes == Long.MIN_VALUE ? Long.MAX_VALUE : Math.abs(bytes);
        if (absB < 1024) {
            return bytes + " B";
        }
        long value = absB;
        var  ci    = new StringCharacterIterator("KMGTPE");
        for (int i = 40; i >= 0 && absB > 0xfffccccccccccccL >> i; i -= 10) {
            value >>= 10;
            ci.next();
        }
        value *= Long.signum(bytes);
        return String.format("%.1f %ciB", value / 1024.0, ci.current());
    }
}
