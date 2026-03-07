# Code Playground - Interactive Input Feature

## Overview
The Code Playground now supports interactive input for code that uses `input()`, `scanf()`, `Scanner`, and other input functions across multiple programming languages.

## How It Works

### 1. Automatic Input Detection
The playground automatically detects if your code requires input by scanning for common input patterns:

**Supported Languages & Patterns:**
- **Python**: `input()`
- **JavaScript**: `prompt()`, `readline()`
- **Java**: `Scanner`, `BufferedReader`, `.nextLine()`, `.nextInt()`
- **C++**: `cin >>`, `scanf()`
- **C**: `scanf()`, `gets()`
- **Go**: `fmt.Scan`, `bufio.NewReader`
- **Ruby**: `gets`, `STDIN.gets`
- **PHP**: `fgets(STDIN)`

### 2. Input Dialog
When you click "Run Code" and the system detects input requirements:
1. An input dialog appears
2. You can enter multiple values (one per line)
3. Click "Run with Input" to execute
4. Or click "Cancel" to go back

### 3. Visual Feedback
- **Input Indicator**: Shows when input is provided with line count
- **Clear Input Button**: Quickly remove all input values
- **Color-coded**: Green indicator for provided input

## Usage Examples

### Example 1: Python Input
```python
name = input("Enter your name: ")
age = input("Enter your age: ")
print(f"Hello {name}, you are {age} years old!")
```

**Input to provide:**
```
John
25
```

**Expected Output:**
```
Hello John, you are 25 years old!
```

### Example 2: Multiple Inputs (Python)
```python
n = int(input("How many numbers? "))
total = 0
for i in range(n):
    num = int(input(f"Enter number {i+1}: "))
    total += num
print(f"Sum: {total}")
```

**Input to provide:**
```
3
10
20
30
```

**Expected Output:**
```
Sum: 60
```

### Example 3: Java Scanner
```java
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter your name: ");
        String name = scanner.nextLine();
        System.out.print("Enter your age: ");
        int age = scanner.nextInt();
        System.out.println("Hello " + name + ", you are " + age + " years old!");
    }
}
```

**Input to provide:**
```
Alice
30
```

### Example 4: C++ Input
```cpp
#include <iostream>
using namespace std;

int main() {
    string name;
    int age;
    
    cout << "Enter your name: ";
    cin >> name;
    cout << "Enter your age: ";
    cin >> age;
    
    cout << "Hello " << name << ", you are " << age << " years old!" << endl;
    return 0;
}
```

**Input to provide:**
```
Bob
28
```

## Features

### ✅ What's Included
- Automatic input detection for 8+ languages
- Multi-line input support
- Visual input indicator
- Clear input functionality
- AI-powered execution simulation with input
- Error handling for missing input

### 🎨 UI Components
1. **Input Dialog**
   - Appears when input is needed
   - Multi-line textarea
   - Example placeholder text
   - Run/Cancel buttons

2. **Input Indicator**
   - Shows when input is provided
   - Displays line count
   - Green success color

3. **Clear Input Button**
   - Red color for visibility
   - Removes all input
   - Hides input dialog

## Technical Implementation

### Frontend (CodePlayground.tsx)

**State Management:**
```typescript
const [userInput, setUserInput] = useState('');
const [showInputDialog, setShowInputDialog] = useState(false);
```

**Input Detection:**
```typescript
const requiresInput = (code: string, lang: string): boolean => {
  const inputPatterns: { [key: string]: RegExp[] } = {
    python: [/input\s*\(/],
    javascript: [/prompt\s*\(/, /readline\s*\(/],
    // ... more patterns
  };
  return patterns.some(pattern => pattern.test(code));
};
```

**Execution Flow:**
```typescript
const executeCode = async () => {
  // Check if input is needed
  if (requiresInput(code, language) && !userInput && !showInputDialog) {
    setShowInputDialog(true);
    return;
  }
  
  // Execute with input
  const response = await fetch(`${apiUrl}/playground/execute`, {
    method: 'POST',
    body: JSON.stringify({ 
      code, 
      language,
      input: userInput || undefined
    })
  });
};
```

### Backend (app.py)

**Request Model:**
```python
class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"
    input: Optional[str] = None
```

**AI Prompt with Input:**
```python
input_context = ""
if req.input:
    input_context = f"\nUser Input (provided):\n{req.input}\n"

prompt = f"""Analyze this {req.language} code and provide:
1. What the code does
2. Expected output when executed{' with the provided input' if req.input else ''}
3. Any syntax errors or runtime errors
4. AI suggestions for improvement

Code:
```{req.language}
{req.code}
```
{input_context}

If the code requires input and input is provided, simulate the execution with that input.
"""
```

**Response Handling:**
```python
# If code requires input but none provided
if result.get("requires_input") and not req.input:
    return {
        "success": False,
        "error": "This code requires input. Please provide input values.",
        "requires_input": True,
        "ai_explanation": "Your code uses input functions..."
    }
```

## User Experience Flow

```
1. User writes code with input()
   ↓
2. User clicks "Run Code"
   ↓
3. System detects input requirement
   ↓
4. Input dialog appears
   ↓
5. User enters values (one per line)
   ↓
6. User clicks "Run with Input"
   ↓
7. Code executes with provided input
   ↓
8. Output displays with AI analysis
   ↓
9. Input indicator shows (green badge)
   ↓
10. User can clear input or run again
```

## Best Practices

### For Users
1. **One value per line**: Enter each input value on a new line
2. **Match expected order**: Provide inputs in the order your code expects
3. **Check data types**: Ensure inputs match expected types (numbers, strings, etc.)
4. **Use examples**: Refer to the placeholder text for guidance

### For Developers
1. **Clear prompts**: Use descriptive input prompts in your code
2. **Error handling**: Add try-catch for invalid inputs
3. **Type conversion**: Convert inputs to correct types (int, float, etc.)
4. **Validation**: Validate input before processing

## Troubleshooting

### Issue: Input dialog doesn't appear
**Solution**: Check if your code uses recognized input patterns. The system looks for `input()`, `scanf()`, `Scanner`, etc.

### Issue: Wrong output with input
**Solution**: 
- Verify input order matches code expectations
- Check for correct data types
- Ensure one value per line

### Issue: Input indicator not showing
**Solution**: Make sure you clicked "Run with Input" and didn't cancel the dialog

### Issue: Can't clear input
**Solution**: Click the red "🗑️ Clear Input" button that appears when input is provided

## Future Enhancements

### Planned Features
- [ ] Input validation before execution
- [ ] Save/load input presets
- [ ] Interactive input during execution (real-time)
- [ ] Input history
- [ ] Auto-detect input format (CSV, JSON, etc.)
- [ ] Bulk input from file upload
- [ ] Input templates for common patterns

### Advanced Features
- [ ] Step-by-step execution with input
- [ ] Visual input flow diagram
- [ ] Input/output test cases
- [ ] Automated testing with multiple inputs
- [ ] Input generation from AI

## Examples by Language

### Python
```python
# Simple input
name = input("Name: ")
print(f"Hello {name}")

# Multiple inputs
x = int(input())
y = int(input())
print(x + y)

# List input
n = int(input())
numbers = [int(input()) for _ in range(n)]
print(sum(numbers))
```

### Java
```java
Scanner sc = new Scanner(System.in);
String name = sc.nextLine();
int age = sc.nextInt();
System.out.println(name + " is " + age);
```

### C++
```cpp
string name;
int age;
cin >> name >> age;
cout << name << " is " << age << endl;
```

### JavaScript (Node.js)
```javascript
const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

rl.question('Name: ', (name) => {
    console.log(`Hello ${name}`);
    rl.close();
});
```

## Testing Checklist

- [ ] Python input() works
- [ ] Java Scanner works
- [ ] C++ cin works
- [ ] Multiple inputs work
- [ ] Input dialog appears correctly
- [ ] Clear input button works
- [ ] Input indicator shows
- [ ] AI analyzes code with input
- [ ] Error handling for missing input
- [ ] Cancel button works

## Summary

The interactive input feature makes the Code Playground truly interactive, allowing users to test code that requires user input across multiple programming languages. The AI-powered execution simulation provides realistic output based on the provided input, making it a powerful learning and testing tool.

**Key Benefits:**
- ✅ Supports 8+ programming languages
- ✅ Automatic input detection
- ✅ Clean, intuitive UI
- ✅ AI-powered execution simulation
- ✅ Visual feedback and indicators
- ✅ Easy input management
