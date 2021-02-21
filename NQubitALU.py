import numpy as np
import qiskit
from qiskit.visualization import plot_state_city
# import qiskit.circuits.library as lib
from qiskit import QuantumRegister
from typing import Optional, List

class HalfAdder(qiskit.circuit.Gate):

    
    def __init__(self) -> None:
        super().__init__('halfAdder', 4, [])

    def _define(self):
        """
        gate halfAdder(a, b, sum, carry)
        {
            cx a, sum;
            cx b, sum;
            ccx a, b, carry;
        }
        """
        from qiskit.circuit.quantumcircuit import QuantumCircuit
        q = qiskit.QuantumRegister(4, name='q')
        qc = qiskit.QuantumCircuit(q, name=self.name)
        # XOR q0, q1 to q2
        qc.cx(0, 2)
        qc.cx(1, 2)

        # AND q0, q1 to q3
        qc.ccx(0, 1, 3)

        self.definition = qc

        # if self.num_variable_qubits < 4:
        #     raise ValueError

class FullAdder(qiskit.circuit.Gate):
    def __init__(self) -> None:
        super().__init__('fullAdder', 8, [])

    def _define(self):
        """
        gate halfAdder(a, b, cin, cout, sum, ancilla1, ancilla2, ancilla3)
        {
            cx a, ancilla1;
            cx b, ancilla1;
            cx cin, cout;
            cx sum, cout;
            ccx a, b, ancilla2;
            ccx cin, ancilla1, ancilla3;
            cx ancilla3, cout;
            cx ancilla2, cout;
            ccx ancilla2, ancilla3, cout;
        }
        """
        from qiskit.circuit.quantumcircuit import QuantumCircuit
        q = qiskit.QuantumRegister(8, name='q')
        qc = qiskit.QuantumCircuit(q, name=self.name)
        # XOR q0, q1 to q5
        qc.cx(0, 5)
        qc.cx(1, 5)

        # XOR q2, q5 to q4
        qc.cx(2, 4)
        qc.cx(5, 4)

        # AND q0, q1 to q6
        qc.ccx(0, 1, 6)

        # AND q2, q5 to q7
        qc.ccx(2, 5, 7)

        # OR q7, q6, q3
        qc.cx(7, 3)
        qc.cx(6, 3)
        qc.ccx(7, 6, 3)

        self.definition = qc

class TwoQubitALU(qiskit.QuantumCircuit):
    def __init__(self,
                 num_qubits: int = 12) -> None:
        """Return a circuit implementing a Two Qubit ALU, with input qubits in the form (a0, a1, b0, b1, s0, s1, c0, c1, sb, ancilla1, ancilla2, ancilla3)

        Args:
            num_qubits: the width of circuit.
            amount: the xor amount in decimal form.
            seed: random seed in case a random xor is requested.

        Raises:
            CircuitError: if the xor bitstring exceeds available qubits.

        Reference Circuit:
            .. jupyter-execute::
                :hide-code:

                from qiskit.circuit.library import XOR
                import qiskit.tools.jupyter
                circuit = XOR(5, seed=42)
                %circuit_library_info circuit
        """
        super().__init__(num_qubits, name="ALU(2)")

        if num_qubits != 12:
            raise ValueError("ALU(2) requires 13 bits")

        q = self.qregs[0]
        # B0 XOR SB to B0 (use ancilla 1, swap b0, ancilla1, then reset ancilla1)
        self.cx(2, 9)
        self.cx(8, 9)
        self.swap(2, 9)
        self.reset([9]*10)

        # B1 XOR SB TO B1 (use ancilla 1, swap b1, ancilla2, then reset ancilla2)
        self.cx(3, 10)
        self.cx(8, 10)
        self.swap(3, 10)
        self.reset([10]*10)

        # (a0, a1, b0, b1, s0, s1, c0, c1, sb, ancilla1, ancilla2, ancilla3)
        # a, b, cin, cout, sum, ancilla1, ancilla2, ancilla3
        # SUM A0, B0, reset ancillas
        self.append(FullAdder(), [q[i] for i in [0, 2, 8, 6, 4, 9, 10, 11]]) #a0, b0, sb, c0, s0, ancillas
        self.reset([9]*10)
        self.reset([10]*10)
        self.reset([11]*10)

        # SUM A1, B1, reset ancillas
        self.append(FullAdder(), [q[i] for i in [1, 3, 6, 7, 5, 9, 10, 11]])
        self.reset([9]*10)
        self.reset([10]*10)
        self.reset([11]*10)

class NQubitALU(qiskit.circuit.library.BlueprintCircuit):
    def __init__(self,
                registerA: qiskit.QuantumRegister,
                registerB: qiskit.QuantumRegister,
                registerS: qiskit.QuantumRegister,
                registerSB: qiskit.QuantumRegister,
                registerC: qiskit.QuantumRegister,
                registerAncilla: qiskit.QuantumRegister,
                num_qubits: Optional[int] = None,
                name: str = 'ALU(N)') -> None:
        """Return a circuit implementing a N Qubit ALU (ALU(N)), with input qubits in the form (a0, a1, b0, b1, s0, s1, c0, c1, sb, ancilla1, ancilla2, ancilla3)

        Args:
            num_qubits: the width of circuit.
            amount: the xor amount in decimal form.
            seed: random seed in case a random xor is requested.

        Raises:
            CircuitError: if the xor bitstring exceeds available qubits.

        Reference Circuit:
            .. jupyter-execute::
                :hide-code:

                from qiskit.circuit.library import XOR
                import qiskit.tools.jupyter
                circuit = XOR(5, seed=42)
                %circuit_library_info circuit
        """
        self.registerA = registerA
        self.registerB = registerB
        self.registerS = registerS
        self.registerSB = registerSB
        self.registerC = registerC
        self.registerAncilla = registerAncilla
        self._num_qubits = None
        self.num_qubits = registerA.size # Size of the Nbits to operate on
        self._name = f'ALU({self.registerA.size})'
        self.qregs = [self.registerA, self.registerB, self.registerS, self.registerSB, self.registerC, self.registerAncilla]
        super().__init__(*self.qregs, name=self._name)
        self.qregs = [self.registerA, self.registerB, self.registerS, self.registerSB, self.registerC, self.registerAncilla]

        
        

    @property
    def num_qubits(self) -> int:
        """The number of qubits to be summed.

        Returns:
            The number of qubits per main register.
        """
        return self._num_qubits

    @num_qubits.setter
    def num_qubits(self, num_qubits: int) -> None:
        """Set the number of qubits in the registers of the ALU operation.

        Args:
            num_qubits: The new number of qubits.
        """
        if self._num_qubits is None or num_qubits != self._num_qubits:
            self._invalidate()
            self._num_qubits = num_qubits
            self._reset_registers()

    def _reset_registers(self):
        qr_A = self.registerA
        qr_B = self.registerB
        qr_S = self.registerS
        qr_SB = self.registerSB
        qr_C = self.registerC
        qr_An = self.registerAncilla
        self.qregs = [qr_A, qr_B, qr_S, qr_SB, qr_C, qr_An]
        # if self.num_carry_qubits > 0:
        #     self.qr_carry = qiskit.QuantumRegister(self.num_carry_qubits, name='carry')
        #     self.qregs += [self.qr_carry]
        # if self.num_ancilla_qubits > 0:
        #     self.qr_ancilla = qiskit.QuantumRegister(self.num_ancilla_qubits, name='ancilla')
        #     self.qregs += [self.qr_ancilla]


    @property
    def num_ancilla_qubits(self) -> int:
        """The number of ancilla qubits required to implement the ALU(operation).

        Returns:
            The number of ancilla qubits in the circuit.
        """
        return 3
            
    @property
    def num_carry_qubits(self) -> int:
        """The number of carry qubits required to compute the ALU.

        Note that this is not necessarily equal to the number of ancilla qubits, these can
        be queried using ``num_ancilla_qubits``.

        Returns:
            The number of carry qubits required to compute the sum.
        """
        return self.num_qubits

    def _check_configuration(self, raise_on_failure=True):
        valid = True
        if self._num_qubits is None:
            valid = False
            if raise_on_failure:
                raise AttributeError('The input register has not been set.')
        return valid

    def _build(self):
        super()._build()

        qr_A = self.registerA
        qr_B = self.registerB
        qr_S = self.registerS
        qr_SB = self.registerSB
        qr_carry = self.registerC
        qr_ancilla = self.registerAncilla
        

        print("Size of qubits: ", qr_A.size, qr_B.size, qr_S.size, qr_SB.size, qr_carry.size, qr_ancilla.size)
        # Initialize B register with SB

        for B_index in range(qr_B.size):
            self.cx(qr_B[B_index], qr_ancilla[0])
            self.cx(qr_SB[0], qr_ancilla[0])
            self.swap(qr_B[B_index], qr_ancilla[0])
            self.reset([qr_ancilla[0]]*1)
        
        for A_index in range(qr_A.size):
            if A_index == 0:
                self.append(FullAdder(), [qubit for qubit in [qr_A[A_index], qr_B[A_index], qr_SB, qr_carry[A_index],
                                                        qr_S[A_index], qr_ancilla[0], qr_ancilla[1], qr_ancilla[2]]]) #a0, b0, sb, c0, s0, ancillas
                print('First adder')
                self.reset([qr_ancilla[0]]*1)
                self.reset([qr_ancilla[1]]*1)
                self.reset([qr_ancilla[2]]*1)
            else:
                print(qr_A[A_index], qr_B[A_index], qr_carry[A_index - 1], qr_carry[A_index],
                                                        qr_S[A_index], qr_ancilla[0], qr_ancilla[1], qr_ancilla[2])
                self.append(FullAdder(), [qubit for qubit in [qr_A[A_index], qr_B[A_index], qr_carry[A_index - 1], qr_carry[A_index],
                                                        qr_S[A_index], qr_ancilla[0], qr_ancilla[1], qr_ancilla[2]]]) #a0, b0, sb, c0, s0, ancillas
                self.reset([qr_ancilla[0]]*1)
                print('Ancilla 1 reset')
                self.reset([qr_ancilla[1]]*1)
                print('Ancilla 2 reset')
                self.reset([qr_ancilla[2]]*1)
                print('Ancilla 3 reset')

if __name__ == "__main__":
    # Import Aer
    from qiskit import Aer
    import qiskit

    import itertools
    # Run the quantum circuit on a statevector simulator backend
    backend = Aer.get_backend('statevector_simulator')

    N = 3
    # Initialize quantum and classic registers
    registerA = qiskit.QuantumRegister(N)
    registerB = qiskit.QuantumRegister(N)
    registerS = qiskit.QuantumRegister(N)
    registerSB = qiskit.QuantumRegister(1)
    registerC = qiskit.QuantumRegister(N)
    registerAnc = qiskit.QuantumRegister(3)
    classicRegister = qiskit.ClassicalRegister(4+4*N)
    regs = [registerA, registerB, registerS, registerSB, registerC, registerAnc]
    flat_regs = list(itertools.chain(*[register[:] for register in regs]))

    # Create a circuit
    circuit = qiskit.QuantumCircuit(*regs, classicRegister,  name = 'ALU')
    
    # Initialize state A = 01, B = 01, SB = 1
    circuit.x(registerA[0])
    circuit.x(registerB[0])
    # circuit.x(registerSB[0])

    # Add NQubitALU to the circuit
    circuit.append(NQubitALU(*regs), flat_regs)

    # Add measurement operations to the circuit
    circuit.measure(range(4+4*N), range(4+4*N))

    # Display the circuit
    print(circuit)

    # Use Aer's qasm_simulator
    simulator = Aer.get_backend('qasm_simulator')

    # Execute the circuit on the qasm simulator
    job = qiskit.execute(circuit, backend, shots=1000)

    # Grab results from the job
    result = job.result()

    # Return counts
    counts = result.get_counts(circuit)
    print("\nInputs are A = 001, B = 001, SB = 1")
    print("\nTotal count for 00 and 11 are:", counts)
    print("\nSum of A + (SB XOR B) is:", counts.most_frequent()[(4+N):(4+2*N)])