export function useInfiniteScroll(loadMore, options = {}) {
    const {
        threshold = 100,
        enabled = true
    } = options
    
    let isLoading = false
    let hasMore = true
    let observer = null
    
    const initObserver = (element) => {
        if (!enabled || !element) return
        
        observer = new IntersectionObserver(
            async (entries) => {
                const entry = entries[0]
                if (entry.isIntersecting && !isLoading && hasMore) {
                    isLoading = true
                    const result = await loadMore()
                    isLoading = false
                    hasMore = result !== false
                }
            },
            { threshold: 0.1, rootMargin: `0px 0px ${threshold}px 0px` }
        )
        
        observer.observe(element)
    }
    
    const destroyObserver = () => {
        if (observer) {
            observer.disconnect()
            observer = null
        }
    }
    
    const reset = () => {
        hasMore = true
        isLoading = false
    }
    
    return {
        initObserver,
        destroyObserver,
        reset,
        get isLoading() { return isLoading },
        get hasMore() { return hasMore }
    }
}