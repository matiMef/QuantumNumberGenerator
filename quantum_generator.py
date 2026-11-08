import scipy.stats as stats
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
import secrets
from collections import Counter
# from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
# from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
import matplotlib.pyplot as plt

# Number Generators
# =========================== CSPRNG ==================================
def generate_csprng_numbers(n_qubits: int, n_shots: int) -> list[int]:
    max_val = 2**n_qubits
    return [secrets.randbelow(max_val) for _ in range(n_shots)]
# =========================== CSPRNG ==================================

# =========================== QRNG ====================================
def generate_dynamic_circuit(n_qubits: int) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits)
    for n in range(n_qubits):
        qc.h(n)
    return qc

def get_results(qc: QuantumCircuit, n_shots: int):
    sampler = StatevectorSampler()
    result = sampler.run([qc], shots=n_shots).result()
    return result

def generate_and_measure(n_qubits: int, n_shots: int) -> list[str]:
    dqc = generate_dynamic_circuit(n_qubits)
    dqc.measure_all()
    results = get_results(dqc, n_shots)
    return results

def generate_and_measure_ibm(n_qubits: int, n_shots: int, backend_name: str = None):
    qc = generate_dynamic_circuit(n_qubits)
    qc.measure_all()
    res = get_results_from_ibm(qc, n_shots, backend_name)
    return res

def bitstrings_to_numbers(results: list[str]) -> list[int]:
    bitstrings = results[0].data.meas.get_bitstrings()
    numbers = [int(b, 2) for b in bitstrings]
    return numbers
# =========================== QRNG ====================================

# =========================== QRNG-IBM ================================
def get_results_from_ibm(qc: QuantumCircuit, n_shots: int, backend_name: str = None):
    service = QiskitRuntimeService(channel="ibm_quantum")
    
    if backend_name:
        backend = service.backend(backend_name)
    else:
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=qc.num_qubits)
    
    print(f"[IBM QPU] Łączenie z fizycznym urządzeniem: {backend.name}")
    
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    isa_circuit = pm.run(qc)
    
    sampler = SamplerV2(backend=backend)
    job = sampler.run([isa_circuit], shots=n_shots)
    print(f"[IBM QPU] Zadanie wysłane! Job ID: {job.job_id()}")
    print("[IBM QPU] Czekam na wykonanie w kolejce...")
    
    result = job.result()
    return result
# =========================== QRNG-IBM ================================

# =========================== Tests =============================
def sample_test(n_bits: int, tests: list[int]):
    results = []
    for test in tests:
        result = generate_and_measure(n_bits, test)
        result = result[0].data.meas.get_counts()
        results.append(result)
    return results

def statictical_distribution(n_bits: int, tests: list[int]):
    results = sample_test(n_bits, tests)
    return results

def run_test(tests: list[int]):
    all_test_results = []
    
    for test in tests:
        result = generate_and_measure(1, test)
        result_list = bitstrings_to_numbers(result)
        
        if not result_list:
            continue
            
        runs = []
        current_len = 1
        
        for i in range(1, len(result_list)):
            if result_list[i] == result_list[i - 1]:
                current_len += 1
            else:
                runs.append({'number': str(result_list[i - 1]), 'length': current_len})
                current_len = 1
        
        runs.append({'number': str(result_list[-1]), 'length': current_len})
        all_test_results.append(runs)
        
    return all_test_results

def run_test_csprng(n_shots: int):
    result_list = generate_csprng_numbers(1, n_shots)
    runs = []
    current_len = 1
    
    for i in range(1, len(result_list)):
        if result_list[i] == result_list[i - 1]:
            current_len += 1
        else:
            runs.append({'number': str(result_list[i - 1]), 'length': current_len})
            current_len = 1
            
    runs.append({'number': str(result_list[-1]), 'length': current_len})
    return runs

def chi_square_test_for_csprng(n_qubits: int, n_shots: int, alpha: float = 0.05):
    numbers = generate_csprng_numbers(n_qubits, n_shots)
    counts = Counter(numbers)
    
    num_states = 2**n_qubits
    observed_counts = [counts.get(i, 0) for i in range(num_states)]

    expected_count = n_shots / num_states
    expected_counts = [expected_count] * num_states
    
    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)
    critical_value = stats.chi2.ppf(1 - alpha, num_states - 1)
    
    print(f"--- TEST CHI-KWADRAT CSPRNG ({n_qubits} bitów, shots: {n_shots}) ---")
    print(f"Statystyka Chi2: {chi2_stat:.4f} | p-value: {p_value:.4f}")
    return chi2_stat, p_value

def chi_square_test_for_quantum_rng(n_qubits: int, n_shots: int, alpha: float = 0.05, sim: bool = True, backend_name = "ibm_brisbane"):
    qc = generate_dynamic_circuit(n_qubits)

    if sim:
        qc.measure_all()
        
        res = get_results(qc, n_shots)
    else:
        res = get_results_from_ibm(qc, n_shots, backend_name)

    counts = res[0].data.meas.get_counts()
    num_states = 2**n_qubits
    observed_counts = []
    
    for i in range(num_states):
        bitstring = format(i, f'0{n_qubits}b')
        observed_counts.append(counts.get(bitstring, 0))
    
    expected_count = n_shots / num_states
    expected_counts = [expected_count] * num_states
    
    chi2_stat, p_value = stats.chisquare(f_obs=observed_counts, f_exp=expected_counts)
    
    degrees_of_freedom = num_states - 1
    critical_value = stats.chi2.ppf(1 - alpha, degrees_of_freedom)
    
    print(f"--- TEST CHI-KWADRAT DLA {n_qubits} KUBITÓW (Shots: {n_shots}) ---")
    print(f"Liczba możliwych stanów (k): {num_states}")
    print(f"Oczekiwana zliczeń na stan: {expected_count}")
    print(f"Statystyka Chi-kwadrat (chi2_emp): {chi2_stat:.4f}")
    print(f"Wartość krytyczna (alpha={alpha}, df={degrees_of_freedom}): {critical_value:.4f}")
    print(f"p-value: {p_value:.4f}")
    
    if chi2_stat <= critical_value:
        print("\nWniosek: BRAK PODSTAW DO ODRZUCENIA H0.")
        print("Generator kwantowy generuje stany zgodnie z idealnym rozkładem jednostajnym.")
    else:
        print("\nWniosek: ODRZUCAMY H0.")
        print("Generator wykazuje istotne statystycznie odchylenie od rozkładu jednostajnego.")
# =========================== Tests =============================

# =========================== Plots =============================
def count_zeros_and_ones_test(n_shots: int):
    # QRNG (1 kubit)
    qrng_numbers = bitstrings_to_numbers(generate_and_measure(1, n_shots))
    qrng_counts = Counter(qrng_numbers)
    
    # CSPRNG (1 bit, zakres 0-1)
    csprng_numbers = generate_csprng_numbers(1, n_shots)
    csprng_counts = Counter(csprng_numbers)
    
    results = {
        'qrng': {0: qrng_counts.get(0, 0), 1: qrng_counts.get(1, 0)},
        'csprng': {0: csprng_counts.get(0, 0), 1: csprng_counts.get(1, 0)}
    }
    
    print(f"\n--- TEST ZLICZANIA ZER I JEDYNEK ({n_shots} prób) ---")
    print(f"QRNG Symulator -> 0: {results['qrng'][0]}, 1: {results['qrng'][1]}")
    print(f"CSPRNG         -> 0: {results['csprng'][0]}, 1: {results['csprng'][1]}")
    
    return results

def plot_statistical_distribution(n_bits: int, tests: list[int]):
    results_list = statictical_distribution(n_bits, tests)
    num_states = 2**n_bits
    states = [format(i, f'0{n_bits}b') for i in range(num_states)]
    
    for idx, shots in enumerate(tests):
        counts = results_list[idx]
        frequencies = [counts.get(s, 0) for s in states]
        
        plt.figure(figsize=(10, 5))
        plt.bar(states, frequencies, color='skyblue', edgecolor='black')
        plt.xlabel('Stan')
        plt.ylabel('Liczba zliczeń')
        plt.title(f'Rozkład statystyczny QRNG Symulator ({shots} prób, {n_bits} bitów)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'results/qrng_sim_distribution_{shots}.png')
        plt.close()

def plot_csprng_distribution(n_bits: int, tests: list[int]):
    num_states = 2**n_bits
    states = [format(i, f'0{n_bits}b') for i in range(num_states)]
    
    for shots in tests:
        numbers = generate_csprng_numbers(n_bits, shots)
        counts = Counter(numbers)
        frequencies = [counts.get(i, 0) for i in range(num_states)]
        
        plt.figure(figsize=(10, 5))
        plt.bar(states, frequencies, color='salmon', edgecolor='black')
        plt.xlabel('Wartość')
        plt.ylabel('Liczba zliczeń')
        plt.title(f'Rozkład statystyczny CSPRNG ({shots} prób, {n_bits} bitów)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'results/csprng_distribution_{shots}.png')
        plt.close()

def plot_runs_test_results(test_shots: int):
    runs_data = run_test([test_shots])[0]
    lengths = [r['length'] for r in runs_data]
    max_len = max(lengths) if lengths else 1
    
    plt.figure(figsize=(8, 5))
    plt.hist(lengths, bins=range(1, max_len + 2), align='left', color='lightgreen', edgecolor='black')
    plt.xlabel('Długość serii')
    plt.ylabel('Częstotliwość występowania')
    plt.title(f'Histogram długości serii (Test serii QRNG, {test_shots} prób)')
    plt.xticks(range(1, max_len + 1))
    plt.tight_layout()
    plt.savefig('results/runs_test_histogram_qrng.png')
    plt.close()

def plot_csprng_runs_test_results(test_shots: int):
    runs_data = run_test_csprng(test_shots)
    lengths = [r['length'] for r in runs_data]
    max_len = max(lengths) if lengths else 1
    
    plt.figure(figsize=(8, 5))
    plt.hist(lengths, bins=range(1, max_len + 2), align='left', color='orange', edgecolor='black')
    plt.xlabel('Długość serii')
    plt.ylabel('Częstotliwość występowania')
    plt.title(f'Histogram długości serii (Test serii CSPRNG, {test_shots} prób)')
    plt.xticks(range(1, max_len + 1))
    plt.tight_layout()
    plt.savefig('results/runs_test_histogram_csprng.png')
    plt.close()

def plot_zeros_and_ones_results(test_shots: int):
    test_data = count_zeros_and_ones_test(test_shots)
    
    labels = ['0', '1']
    
    qrng_vals = [test_data['qrng'][0], test_data['qrng'][1]]
    plt.figure(figsize=(6, 5))
    plt.bar(labels, qrng_vals, color=['skyblue', 'deepskyblue'], edgecolor='black')
    plt.xlabel('Wartość bitu')
    plt.ylabel('Liczba zliczeń')
    plt.title(f'Zliczenia 0 i 1 - QRNG Symulator ({test_shots} prób)')
    plt.tight_layout()
    plt.savefig('results/zeros_ones_qrng.png')
    plt.close()
    
    csprng_vals = [test_data['csprng'][0], test_data['csprng'][1]]
    plt.figure(figsize=(6, 5))
    plt.bar(labels, csprng_vals, color=['salmon', 'darksalmon'], edgecolor='black')
    plt.xlabel('Wartość bitu')
    plt.ylabel('Liczba zliczeń')
    plt.title(f'Zliczenia 0 i 1 - CSPRNG ({test_shots} prób)')
    plt.tight_layout()
    plt.savefig('results/zeros_ones_csprng.png')
    plt.close()

def plot_ibm_statistical_distribution(n_bits: int, tests: list[int], backend_name: str = None):
    num_states = 2**n_bits
    states = [format(i, f'0{n_bits}b') for i in range(num_states)]
    
    for shots in tests:
        res = generate_and_measure_ibm(n_bits, shots, backend_name)
        counts = res[0].data.meas.get_counts()
        frequencies = [counts.get(s, 0) for s in states]
        
        plt.figure(figsize=(10, 5))
        plt.bar(states, frequencies, color='purple', edgecolor='black')
        plt.xlabel('Stan')
        plt.ylabel('Liczba zliczeń')
        plt.title(f'Rozkład statystyczny IBM QRNG ({shots} prób, {n_bits} bitów)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'results/ibm_qrng_distribution_{shots}.png')
        plt.close()

def plot_ibm_zeros_and_ones_results(test_shots: int, backend_name: str = None):
    res = generate_and_measure_ibm(1, test_shots, backend_name)
    counts = res[0].data.meas.get_counts()
    
    val_0 = counts.get('0', 0)
    val_1 = counts.get('1', 0)
    
    labels = ['0', '1']
    vals = [val_0, val_1]
    
    plt.figure(figsize=(6, 5))
    plt.bar(labels, vals, color=['mediumpurple', 'rebeccapurple'], edgecolor='black')
    plt.xlabel('Wartość bitu')
    plt.ylabel('Liczba zliczeń')
    plt.title(f'Zliczenia 0 i 1 - IBM QRNG ({test_shots} prób)')
    plt.tight_layout()
    plt.savefig('results/ibm_zeros_ones.png')
    plt.close()
# =========================== Plots =============================

def main():
    print("Uruchamianie testów i generowanie wykresów...")
    
    test_variants = [10000, 100000, 1000000]
    n_bits = 4
    
    # 1. Test Chi-kwadrat
    print("\n[--- TESTY CHI-KWADRAT ---]")
    chi_square_test_for_quantum_rng(n_qubits=n_bits, n_shots=10000, sim=True)
    chi_square_test_for_csprng(n_qubits=n_bits, n_shots=10000)

    # 2. Rozkład statystyczny 10000 oraz 100000 liczb
    print("\n[--- ROZKŁADY STATYSTYCZNE I WIELOKROTNE GENEROWANIE ---]")
    plot_statistical_distribution(n_bits, test_variants)
    plot_csprng_distribution(n_bits, test_variants)
    
    # 3. Test serii
    print("\n[--- TEST SERII ---]")
    print(run_test([1000]))
    plot_runs_test_results(1000)
    plot_csprng_runs_test_results(1000)
    
    # 4. Nowy test zliczania zera i jedynek (zakres 0 i 1)
    print("\n[--- TEST ZLICZANIA ZER I JEDYNEK ---]")
    plot_zeros_and_ones_results(10000)
    
    print("\nZakończono pomyślnie.")

if __name__ == "__main__":
    main()
