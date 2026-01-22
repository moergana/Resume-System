package org.kira.resumesystem.utils;

import io.lettuce.core.api.StatefulConnection;
import io.lettuce.core.codec.ByteArrayCodec;
import io.lettuce.core.codec.RedisCodec;
import io.lettuce.core.output.CommandOutput;
import io.lettuce.core.output.StatusOutput;
import io.lettuce.core.protocol.AsyncCommand;
import io.lettuce.core.protocol.Command;
import io.lettuce.core.protocol.CommandArgs;
import io.lettuce.core.protocol.ProtocolKeyword;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.DecoratedRedisConnection;
import org.springframework.data.redis.connection.RedisConnection;
import org.springframework.data.redis.connection.lettuce.LettuceConnection;
import org.springframework.data.redis.core.RedisCallback;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Future;

import static org.kira.resumesystem.utils.RedisConstants.*;

/**
 * 基于Redis中的 Cuckoo Filter（布谷鸟过滤器）的工具类，封装了常用的操作方法
 * 相比于传统的布隆过滤器，Cuckoo Filter 支持删除操作，并且在高负载下具有更好的查询性能
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class RedisCuckooFilterTool {
    private final StringRedisTemplate stringRedisTemplate;

    /**
     * 自定义Cuckoo Filter命令
     * 实现ProtocolKeyword接口以便与Lettuce的命令调度机制兼容
     */
    private static class CuckooCommand implements ProtocolKeyword {
        private final String name;
        private final byte[] bytes;

        public CuckooCommand(String name) {
            // Store name and its byte representation
            this.name = name;
            this.bytes = name.getBytes(StandardCharsets.UTF_8);
        }

        @Override
        public byte[] getBytes() {
            return bytes;
        }

        @Override
        public String name() {
            return name;
        }
    }

    // 定义Cuckoo Filter相关命令
    private static final CuckooCommand CF_RESERVE = new CuckooCommand("CF.RESERVE");
    private static final CuckooCommand CF_ADD = new CuckooCommand("CF.ADD");
    private static final CuckooCommand CF_ADDNX = new CuckooCommand("CF.ADDNX");
    private static final CuckooCommand CF_INSERT = new CuckooCommand("CF.INSERT");
    private static final CuckooCommand CF_EXISTS = new CuckooCommand("CF.EXISTS");
    private static final CuckooCommand CF_DEL = new CuckooCommand("CF.DEL");

    /**
     * Custom Output to handle Integer or Boolean response (common in RESP3/Module commands).
     * Maps boolean true -> 1L, false -> 0L.
     * 由于新的 Redis Stack / 模块在 RESP3 协议下，对于布谷鸟过滤器操作返回的是布尔值（Boolean）而不是整数（Integer）。
     * 而 Lettuce 默认的 ArrayOutput 以及之前尝试的 output 都不支持 set(boolean)，从而会导致 UnsupportedOperationException。
     * 因此需要自定义一个 Output 来处理这种情况。
     */
    private static class IntegerOrBooleanOutput extends CommandOutput<byte[], byte[], Long> {
        public IntegerOrBooleanOutput(RedisCodec<byte[], byte[]> codec) {
            super(codec, null);
        }

        @Override
        public void set(long integer) {
            output = integer;
        }

        @Override
        public void set(boolean value) {
            output = value ? 1L : 0L;
        }
    }

    /**
     * Custom Output to handle list of results which can be Integers or Booleans (e.g. CF.INSERT).
     */
    private static class ObjectListOutput extends CommandOutput<byte[], byte[], List<Object>> {
        private boolean initialized;

        public ObjectListOutput(RedisCodec<byte[], byte[]> codec) {
            super(codec, new ArrayList<>());
        }

        @Override
        public void set(long integer) {
            output.add(integer);
        }

        @Override
        public void set(boolean value) {
            output.add(value);
        }

        @Override
        public void multi(int count) {
            if (!initialized) {
                output = new ArrayList<>(count);
                initialized = true;
            }
        }
    }

    /**
     * 通用的命令调度方法，适配不同类型的Lettuce连接
     * @param nativeConnection Lettuce的原生连接对象
     * @param type 命令类型
     * @param output 命令输出处理器
     * @param args 命令参数
     * @return 命令执行结果
     * @param <T> 命令结果类型
     */
    @SuppressWarnings("unchecked")
    private <T> T dispatch(Object nativeConnection, ProtocolKeyword type, CommandOutput<byte[], byte[], T> output, CommandArgs<byte[], byte[]> args) {
        try {
            if (nativeConnection instanceof StatefulConnection) {
                StatefulConnection<byte[], byte[]> connection = (StatefulConnection<byte[], byte[]>) nativeConnection;
                AsyncCommand<byte[], byte[], T> command = new AsyncCommand<>(new Command<>(type, output, args));
                connection.dispatch(command);
                return command.get();
            }

            // Fallback: try reflection if not StatefulConnection (unlikely for Lettuce)
            try {
                Method method = nativeConnection.getClass().getMethod("dispatch", ProtocolKeyword.class, CommandOutput.class, CommandArgs.class);
                Future<T> future = (Future<T>) method.invoke(nativeConnection, type, output, args);
                return future.get();
            } catch (NoSuchMethodException e) {
                throw new UnsupportedOperationException("Native connection " + nativeConnection.getClass().getName() + " does not support " + type.name(), e);
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to execute " + type.name(), e);
        }
    }

    /**
     * 获取Lettuce的原生连接对象
     * @param connection Spring Data Redis的RedisConnection对象
     * @return Lettuce的原生连接对象，或null如果不是Lettuce连接
     */
    private Object getLettuceNativeConnection(RedisConnection connection) {
        while (connection instanceof DecoratedRedisConnection) {
            connection = ((DecoratedRedisConnection) connection).getDelegate();
        }
        if (connection instanceof LettuceConnection) {
            return ((LettuceConnection) connection).getNativeConnection();
        }
        return null;
    }

    /**
     * 在Redis中为指定的key创建一个Cuckoo Filter，设置其容量
     * @param key Cuckoo Filter的key
     * @param capacity 预期存储的元素数量
     * @return 如果创建成功返回true，否则返回false
     */
    public boolean reserve(String key, long capacity) {
        return Boolean.TRUE.equals(stringRedisTemplate.execute((RedisCallback<Boolean>) connection -> {
            // 获取Lettuce的原生连接对象
            Object nativeConnection = getLettuceNativeConnection(connection);
            if (nativeConnection != null) {
                // 构建CF.RESERVE命令的参数
                CommandArgs<byte[], byte[]> args = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                        .addKey(key.getBytes())
                        .add(String.valueOf(capacity).getBytes())
                        .add("BUCKETSIZE".getBytes()).add(CUCKOO_FILTER_BUCKETSIZE.toString().getBytes())
                        .add("MAXITERATIONS".getBytes()).add(CUCKOO_FILTER_MAXITERATIONS.toString().getBytes())
                        .add("EXPANSION".getBytes()).add(CUCKOO_FILTER_EXPANSION.toString().getBytes());

                try {
                    // 通过dispatch方法，利用Lettuce执行CF.RESERVE命令
                    String result = dispatch(nativeConnection, CF_RESERVE, new StatusOutput<>(ByteArrayCodec.INSTANCE), args);
                    return "OK".equals(result);
                } catch (Exception e) {
                    log.error("Failed to reserve Cuckoo Filter for key {} with capacity {}", key, capacity);
                    // 判断一下是否是由于Filter已存在引起的错误
                    Boolean hasKey = stringRedisTemplate.hasKey(key);
                    // 如果是Filter已存在，则记录简单的错误日志
                    if (hasKey != null && hasKey) {
                        log.error("Cuckoo Filter with key {} already exists.", key);
                    }
                    // 如果是其他错误，则打印完整的异常堆栈以便排查，并抛出异常
                    else {
                        log.debug("Error details: ", e);
                        throw e;
                    }
                    return false;
                }
            }
            log.warn("Connection is not LettuceConnection (found: {}), cannot execute CF.RESERVE", connection.getClass().getName());
            return false;
        }));
    }

    /**
     * 向指定的Cuckoo Filter中添加一个元素
     * @param key Cuckoo Filter的key
     * @param value 要添加的元素值
     * @return 如果添加成功返回true，否则返回false
     */
    public boolean add(String key, String value) {
        return Boolean.TRUE.equals(stringRedisTemplate.execute((RedisCallback<Boolean>) connection -> {
            Object nativeConnection = getLettuceNativeConnection(connection);
            if (nativeConnection != null) {
                CommandArgs<byte[], byte[]> args = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                        .addKey(key.getBytes())
                        .add(value.getBytes());

                try {
                    Long result = dispatch(nativeConnection, CF_ADD, new IntegerOrBooleanOutput(ByteArrayCodec.INSTANCE), args);
                    return Long.valueOf(1).equals(result);
                } catch (Exception e) {
                    log.error("Error executing CF.ADD", e);
                    return false;
                }
            }
            return false;
        }));
    }

    /**
     * 向指定的Cuckoo Filter中添加一个元素，仅当该元素不存在时才添加
     * @param key Cuckoo Filter的key
     * @param value 要添加的元素值
     * @return 如果添加成功返回true，否则返回false
     */
    public boolean addnx(String key, String value) {
        return Boolean.TRUE.equals(stringRedisTemplate.execute((RedisCallback<Boolean>) connection -> {
            Object nativeConnection = getLettuceNativeConnection(connection);
            if (nativeConnection != null) {
                CommandArgs<byte[], byte[]> args = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                        .addKey(key.getBytes())
                        .add(value.getBytes());

                try {
                    Long result = dispatch(nativeConnection, CF_ADDNX, new IntegerOrBooleanOutput(ByteArrayCodec.INSTANCE), args);
                    return Long.valueOf(1).equals(result);
                } catch (Exception e) {
                    log.error("Error executing CF.ADDNX", e);
                    return false;
                }
            }
            return false;
        }));
    }

    /**
     * 批量添加元素到指定的Cuckoo Filter中
     * @param key Cuckoo Filter的key
     * @param values 要添加的元素列表
     */
    @SuppressWarnings("unchecked")
    public void batchAdd(String key, List<String> values) {
        // 为了避免一次性Add太多元素导致内存占用过大，采用分批处理的方式
        int batchSize = 1000;   // 每批处理的元素数量
        try {
            for(int i=0; i < values.size(); i += batchSize) {
                int end = Math.min(i + batchSize, values.size());
                List<String> batch = values.subList(i, end);

                stringRedisTemplate.execute((RedisCallback<Void>) connection -> {
                    Object nativeConnection = getLettuceNativeConnection(connection);
                    if (nativeConnection != null) {
                        // 构建CF.INSERT命令的参数。该命令格式为：CF.INSERT key ITEMS item1 item2 ...
                        // 其中ITEMS表示后续跟随的是多个元素，可以一次性插入多个元素
                        CommandArgs<byte[], byte[]> args = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                                .addKey(key.getBytes())
                                .add("ITEMS".getBytes());

                        // 将每个元素添加到命令参数中
                        for (String v : batch) {
                            args.add(v.getBytes());
                        }

                        // CF.INSERT returns Integer[] or Boolean[]
                        List<Object> results = dispatch(nativeConnection, CF_INSERT, new ObjectListOutput(ByteArrayCodec.INSTANCE), args);

                        // Process results if needed (logging failures etc)
                        if (results != null) {
                            // 这里的CF.INSERT返回的结果类型可能是Long或Boolean，需要根据实际返回类型进行处理
                            // 验证每个元素的插入结果
                            for (int j = 0; j < results.size(); j++) {
                                Object res = results.get(j);
                                if (res instanceof Long) {
                                    if (!Long.valueOf(1).equals(res)) {
                                        log.error("Item {} not added during batch insert", batch.get(j));
                                    }
                                } else if (res instanceof Boolean) {
                                    if (!((Boolean) res)) {
                                        log.error("Item {} not added during batch insert", batch.get(j));
                                    }
                                }
                            }
                        }
                    }
                    return null;
                });

                log.info("Batch inserted {} elements to Cuckoo Filter with key {}", batch.size(), key);
            }
        } catch (Exception e) {
            log.error("Error during batch insert to Cuckoo Filter with key {}: {}", key, e.getMessage());
            throw new RuntimeException(e);
        }
    }

    /**
     * 检查指定的元素是否存在于Cuckoo Filter中
     * @param key Cuckoo Filter的key
     * @param value 要检查的元素值
     * @return 如果元素存在返回true，否则返回false
     */
    public boolean exists(String key, String value) {
        return Boolean.TRUE.equals(stringRedisTemplate.execute((RedisCallback<Boolean>) connection -> {
            Object nativeConnection = getLettuceNativeConnection(connection);
            if (nativeConnection != null) {
                CommandArgs<byte[], byte[]> args = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                        .addKey(key.getBytes())
                        .add(value.getBytes());

                try {
                    Long result = dispatch(nativeConnection, CF_EXISTS, new IntegerOrBooleanOutput(ByteArrayCodec.INSTANCE), args);
                    return Long.valueOf(1).equals(result);
                } catch (Exception e) {
                    log.error("Error executing CF.EXISTS", e);
                    return false;
                }
            }
            return false;
        }));
    }

    /**
     * 从指定的Cuckoo Filter中删除一个元素
     * @param key Cuckoo Filter的key
     * @param value 要删除的元素值
     * @return 如果删除成功返回true，否则返回false
     */
    public boolean delete(String key, String value) {
        return Boolean.TRUE.equals(stringRedisTemplate.execute((RedisCallback<Boolean>) connection -> {
            Object nativeConnection = getLettuceNativeConnection(connection);
            if (nativeConnection != null) {
                CommandArgs<byte[], byte[]> args = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                        .addKey(key.getBytes())
                        .add(value.getBytes());

                try {
                    Long result = dispatch(nativeConnection, CF_DEL, new IntegerOrBooleanOutput(ByteArrayCodec.INSTANCE), args);
                    return Long.valueOf(1).equals(result);
                } catch (Exception e) {
                    log.error("Error executing CF.DEL", e);
                    return false;
                }
            }
            return false;
        }));
    }

    /**
     * 批量从指定的Cuckoo Filter中删除元素
     * @param key Cuckoo Filter的key
     * @param values 要删除的元素列表
     */
    public void batchDelete(String key, List<String> values) {
        int batchSize = 1000;
        try {
            for (int i = 0; i < values.size(); i += batchSize) {
                int end = Math.min(i + batchSize, values.size());
                List<String> batch = values.subList(i, end);

                stringRedisTemplate.execute((RedisCallback<Void>) connection -> {
                    Object nativeConnection = getLettuceNativeConnection(connection);
                    if (nativeConnection instanceof StatefulConnection) {
                        try {
                            // 将连接转换为StatefulConnection以支持命令流水线
                            @SuppressWarnings("unchecked")
                            StatefulConnection<byte[], byte[]> statefulConnection = (StatefulConnection<byte[], byte[]>) nativeConnection;
                            // 禁用自动刷新以启用命令流水线
                            statefulConnection.setAutoFlushCommands(false); // Enable pipelining

                            // 存储所有的异步命令Future
                            List<AsyncCommand<byte[], byte[], Long>> futures = new ArrayList<>();

                            // 为每个元素创建CF.DEL的异步命令并调度
                            for (String value : batch) {
                                CommandArgs<byte[], byte[]> args = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                                        .addKey(key.getBytes())
                                        .add(value.getBytes());

                                Command<byte[], byte[], Long> cmd = new Command<>(CF_DEL, new IntegerOrBooleanOutput(ByteArrayCodec.INSTANCE), args);
                                AsyncCommand<byte[], byte[], Long> asyncCmd = new AsyncCommand<>(cmd);

                                statefulConnection.dispatch(asyncCmd);
                                futures.add(asyncCmd);
                            }

                            // 将一个批次的命令一次性发送到Redis服务器，避免每个命令单独发送的网络开销
                            statefulConnection.flushCommands(); // Send all commands at once

                            // Wait for completion
                            // 检查每个删除命令的结果
                            for (int j = 0; j < futures.size(); j++) {
                                AsyncCommand<byte[], byte[], Long> f = futures.get(j);
                                String val = batch.get(j);
                                try {
                                    if (!Long.valueOf(1).equals(f.get())) {
                                        // 获取该命令未能删除的元素值并用日志记录，便于后续排查修复
                                        log.error("Item '{}' not deleted or not found during batch delete", val);
                                    }
                                } catch (Exception e) {
                                    log.error("Error in batch delete future for item '{}'", val, e);
                                }
                            }
                        } finally {
                            /* 这里的try没有catch块，如果批量删除的过程中出现异常，异常会被外层的try-catch捕获 */
                            // Restore auto-flush
                            // 无论是否删除出现异常，都必须要恢复自动刷新设置
                            ((StatefulConnection<?, ?>) nativeConnection).setAutoFlushCommands(true);
                        }
                    } else {
                        log.warn("Connection is not Lettuce StatefulConnection, cannot execute batch CF.DEL");
                    }
                    return null;
                });
                log.info("Batch deleted {} elements from Cuckoo Filter with key {}", batch.size(), key);
            }
        } catch (Exception e) {
            log.error("Error during batch delete from Cuckoo Filter with key {}: {}", key, e.getMessage());
            throw new RuntimeException(e);
        }
    }
}
