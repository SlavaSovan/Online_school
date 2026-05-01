<template>
    <div class="home">
        <section class="hero">
            <h1>Добро пожаловать в Онлайн-школу!</h1>
            <p>Лучшее место для обучения и развития</p>
        </section>
        
        <section class="features">
            <div class="feature-card">
                <h3>Доступные курсы</h3>
                <p>Широкий выбор курсов по различным направлениям</p>
            </div>
            <div class="feature-card">
                <h3>Опытные преподаватели</h3>
                <p>Учитесь у лучших специалистов в своей области</p>
            </div>
                <div class="feature-card">
                <h3>Удобный формат</h3>
                <p>Занимайтесь в любое время в удобном для вас темпе</p>
            </div>
        </section>
    </div>
</template>

<style scoped>
.home {
    max-width: 1200px;
    margin: 0 auto;
}

.hero {
    text-align: center;
    padding: 4rem 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    padding: 2rem;
}

.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}

.feature-card h3 {
    margin-bottom: 1rem;
    color: #2c3e50;
}
</style>