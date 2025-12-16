import redis

client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

try:
    client.ping()
    print("Успешное подключение к Redis")
    
    client.set("user:name", "Иван")
    name = client.get("user:name")

    client.setex("session:123", 3600, "active")

    client.set("counter", 0)
    client.incr("counter")
    client.incrby("counter", 5)
    client.decr("counter") 
    current_counter = client.get("counter")
    
    client.delete("tasks")

    client.lpush("tasks", "task1", "task2")
    client.rpush("tasks", "task3", "task4")
    
    tasks = client.lrange("tasks", 0, -1)
    first_task = client.lpop("tasks")
    last_task = client.rpop("tasks")
    length = client.llen("tasks")

    client.delete("tags", "languages")
    
    client.sadd("tags", "python", "redis", "database")
    client.sadd("languages", "python", "java", "javascript")
    
    is_member = client.sismember("tags", "python")
    
    all_tags = client.smembers("tags")
    
    intersection = client.sinter("tags", "languages")
    union = client.sunion("tags", "languages")
    difference = client.sdiff("tags", "languages")

    client.hset("user:1000", mapping={
        "name": "Иван",
        "age": "30",
        "city": "Москва"
    })

    user_name = client.hget("user:1000", "name")
    all_data = client.hgetall("user:1000")
    

    exists = client.hexists("user:1000", "email")
    

    keys = client.hkeys("user:1000")
    values = client.hvals("user:1000")

    client.delete("leaderboard")

    client.zadd("leaderboard", {
        "player1": 100,
        "player2": 200,
        "player3": 150
    })
    
    top_players = client.zrange("leaderboard", 0, 2, withscores=True)
    
    players_by_score = client.zrangebyscore("leaderboard", 100, 200)

    rank = client.zrank("leaderboard", "player1")

    print("\n--- Результаты работы ---")
    print(f"Имя пользователя: {name}")
    print(f"Текущее значение счетчика: {current_counter}")
    print(f"Список задач после операций: {tasks}")
    print(f"Первая задача: {first_task}, Последняя задача: {last_task}")
    print(f"Длина списка задач: {length}")
    print(f"Элемент 'python' в tags: {is_member}")
    print(f"Все теги: {all_tags}")
    print(f"Пересечение множеств: {intersection}")
    print(f"Данные пользователя: {all_data}")
    print(f"Ключи хеша: {keys}")
    print(f"Значения хеша: {values}")
    print(f"Топ игроков: {top_players}")
    print(f"Игроки с оценкой 100-200: {players_by_score}")
    print(f"Ранг player1: {rank}")

except redis.ConnectionError as e:
    print(f"Ошибка подключения к Redis: {e}")
except Exception as e:
    print(f"Произошла ошибка: {e}")
finally:

    client.close()
    print("\nСоединение с Redis закрыто")