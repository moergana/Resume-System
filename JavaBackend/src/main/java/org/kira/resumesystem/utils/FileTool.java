package org.kira.resumesystem.utils;
import java.nio.file.Path;

public class FileTool {
    /**
     * 将本地文件路径修改为WSL内等价的访问路径
     * @param path 本地文件路径
     * @return WSL内的访问路径
     */
    public static String parsePath(String path) {
        // 将本地的文件路径修改为wsl内的等价的访问路径
        // 具体修改方法：将盘符修改为小写字母，同时在前面加上/mnt/
        // 例如：C:\Users\kira\file.txt -> /mnt/c/Users/kira/file.txt

        // 如果path为空，直接返回
        if (path == null || path.isEmpty()) {
            return path;
        }
        String wslPath = path.replace("\\", "/");
        char driveLetter = Character.toLowerCase(wslPath.charAt(0));
        wslPath = "/mnt/" + driveLetter + wslPath.substring(2);
        return wslPath;
    }

    /**
     * 从存储的文件路径中提取原始文件名
     * @param filePath 存储的文件路径
     * @return 原始文件名
     */
    public static String getOriginalFileName(String filePath) {
        // 从存储的文件名中提取原始文件名
        // 存储的文件名格式为：Path/<originalFileName>_<UUID>.pdf，最终需要得到<originalFileName>.pdf
        if (filePath == null || filePath.isEmpty()) {
            return "";
        }
        Path path = Path.of(filePath);
        String fileName = path.getFileName().toString();
        int dot_index = fileName.indexOf('.');
        String extension = "";
        if (dot_index == -1) {
            extension = "";
        }
        else {
            extension = fileName.substring(dot_index);
        }
        String originalFileName = fileName.substring(0, fileName.lastIndexOf('_')) + extension;
        return originalFileName;
    }
}
