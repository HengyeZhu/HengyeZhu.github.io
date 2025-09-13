title: Differences between rocRand and cuRand when using HIP
date: September 12, 2025
author: Hengye Zhu
category: GeNN

In cuRand, the state of an RNG is a plain struct e.g. for XORWOW:

```c
struct curandStateXORWOW {
    unsigned int d, v[5];
    int boxmuller_flag;
    int boxmuller_flag_double;
    float boxmuller_extra;
    double boxmuller_extra_double;
};
```

whereas, in [rocRand](https://github.com/ROCm/rocm-libraries/blob/develop/projects/rocrand/library/include/rocrand/rocrand_xorwow.h), the implementation is a lot more C++:

```c
class xorwow_engine
{
public:
    struct xorwow_state
    {
        unsigned int d;

    #ifndef ROCRAND_DETAIL_BM_NOT_IN_STATE

        unsigned int boxmuller_float_state; 
        unsigned int boxmuller_double_state; 
        float boxmuller_float; 
        double boxmuller_double; 
    #endif
        unsigned int x[5];
    };

    __forceinline__ __device__ __host__ xorwow_engine(const unsigned long long seed,
                                                      const unsigned long long subsequence,
                                                      const unsigned long long offset)
    {
        m_state.x[0] = 123456789U;
        m_state.x[1] = 362436069U;
        m_state.x[2] = 521288629U;
        m_state.x[3] = 88675123U;
        m_state.x[4] = 5783321U;

        m_state.d = 6615241U;

        const unsigned int s0 = static_cast<unsigned int>(seed) ^ 0x2c7f967fU;
        const unsigned int s1 = static_cast<unsigned int>(seed >> 32) ^ 0xa03697cbU;
        const unsigned int t0 = 1228688033U * s0;
        const unsigned int t1 = 2073658381U * s1;
        m_state.x[0] += t0;
        m_state.x[1] ^= t0;
        m_state.x[2] += t1;
        m_state.x[3] ^= t1;
        m_state.x[4] += t0;
        m_state.d += t1 + t0;

        discard_subsequence(subsequence);
        discard(offset);
    }

protected:
    xorwow_state m_state;
}; 
```

1.When using AMD GPUs, you can't create classes with __device__ hiprandState d_rng; as that would mean the constructor needs to be run on device when the kernel is loaded which is understandably not possible.

2.You can't freely hack with the internals of the RNG state as they don't even provide a getter for the state struct which, irritatingly, is sitting there in m_state protected member.

To solve the first problem, we can switch global variable to pointer and allocate manually. For example:
```c
void Backend::genAllocateMemPreamble(CodeStream &os, const ModelSpecMerged &modelMerged) const
{
    // If global RNG is required
    if(isGlobalDeviceRNGRequired(modelMerged.getModel())) {
        CodeStream::Scope b(os);

        // Allocate memory
        os << "hiprandStatePhilox4_32_10_t *hostPtr;" << std::endl;
        os << "CHECK_RUNTIME_ERRORS(hipMalloc(&hostPtr, sizeof(hiprandStatePhilox4_32_10_t)));" << std::endl;

        // Copy to device symbol
        os << "CHECK_RUNTIME_ERRORS(hipMemcpyToSymbol(HIP_SYMBOL(d_rng), &hostPtr, sizeof(void*)));" << std::endl;
    }
}
```

Finally, I would like to thank Dr. James Knight for his tremendous help throughout this process!