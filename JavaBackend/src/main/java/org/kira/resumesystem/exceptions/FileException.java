package org.kira.resumesystem.exceptions;

public class FileException extends CommonException{

    public FileException(String message) {
        super(message, 500);
    }

    public FileException(Throwable cause) {
        super(cause, 500);
    }

    public FileException(String message, Throwable cause) {
        super(message, cause, 500);
    }
}
