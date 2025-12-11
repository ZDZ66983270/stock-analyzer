/**
 * 星级评分组件
 * 将0-100的分数转换为星级显示
 */
function StarRating({ score = 0 }) {
    const stars = Math.round(score / 20); // 0-100 转换为 0-5星

    return (
        <div style={{
            display: 'flex',
            gap: '0.2rem',
            fontSize: '1.2rem'
        }}>
            {[...Array(5)].map((_, i) => (
                <span
                    key={i}
                    style={{
                        color: i < stars ? '#fbbf24' : '#52525b'
                    }}
                >
                    {i < stars ? '⭐' : '☆'}
                </span>
            ))}
        </div>
    );
}

export default StarRating;
