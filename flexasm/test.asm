
	move sp, stack
	call main
infloop:
	jump infloop

main:
	call allocInit
	move ax, 64
	call allocBytes
	move fx, ax		;Keep address of buffer
mainloop:
	move ax, fx
	call getString

	move ax, fx
	call parseExpression
	move gx, ax

	move ax, fx
	call printString
	move cx, 61
	out cx, 0

	move bx, gx
	call evalExpression
	call printNumber
	move cx, 0xA
	out cx, 0

	jump mainloop

	return


evalTable:
	dw infloop
	dw evalNumber
	dw evalAdd
	dw evalSub
	dw evalMul
	dw evalDiv
	dw evalMod
evalExpression:		;[Param BX, returns AX, uses AX-CX]
	load ax, bx
	add ax, evalTable
	jumpi ax
evalNumber:
	load ax, bx+1
	return
evalAdd:
	push bx
	load bx, bx+1
	call evalExpression
	pop bx
	load bx, bx+2
	push ax
	call evalExpression
	pop bx
	add ax, bx
	return
evalSub:
	push bx
	load bx, bx+1
	call evalExpression
	pop bx
	load bx, bx+2
	push ax
	call evalExpression
	pop bx
	sub bx, ax
	move ax, bx
	return
evalMul:
	push bx
	load bx, bx+1
	call evalExpression
	pop bx
	load bx, bx+2
	push ax
	call evalExpression
	pop bx
	call multiplyNumbers
	return
evalDiv:
	push bx
	load bx, bx+1
	call evalExpression
	pop bx
	load bx, bx+2
	push ax
	call evalExpression
	move bx, ax
	pop ax
	call divideNumbers
	return
evalMod:
	push bx
	load bx, bx+1
	call evalExpression
	pop bx
	load bx, bx+2
	push ax
	call evalExpression
	move bx, ax
	pop ax
	call divideNumbers
	move ax, bx
	return


multiplyNumbers:	;[Param AX-BX, returns AX, uses AX-CX]
	jng ax, bx , multiplyNoSwap
	move cx, bx
	move bx, ax
	jump multiplyGo
multiplyNoSwap:
	move cx, ax
multiplyGo:
	move ax, 0
	je cx, 0, multiplyDone
multiplyLoop:
	sub cx, 1
	add ax, bx
	jg cx, 0, multiplyLoop
multiplyDone:
	return


divideNumbers:	;[Param AX-BX, returns AX-BX, uses AX-CX]
	move cx, bx
	move bx, ax
	move ax, 0
	je cx, 0, divideDone
	jl bx, cx, divideDone
divideLoop:
	sub bx, cx
	add ax, 1
	jnl bx, cx, divideLoop
divideDone:
	return


parseExpression:	;[Param AX, returns AX, uses AX-EX, GX]
	move gx, ax
	call parseAdd
	return


parseAdd:			;[Param GX, returns AX]
	call parseMultiply
parseAdd2:
	load bx, gx
	je bx, 43, parseAddPlus
	je bx, 45, parseAddMinus
	return
parseAddPlus:
	add gx, 1
	move ex, ax
	move ax, 3
	call allocBytes
	je ax, 0, infloop
	store ex, ax+1
	move bx, 2		;Addition
	store bx, ax
	push ax
	call parseMultiply
	pop ex
	store ax, ex+2
	move ax, ex
	jump parseAdd2
parseAddMinus:
	add gx, 1
	move ex, ax
	move ax, 3
	call allocBytes
	je ax, 0, infloop
	store ex, ax+1
	move bx, 3		;Subtraction
	store bx, ax
	push ax
	call parseMultiply
	pop ex
	store ax, ex+2
	move ax, ex
	jump parseAdd2


parseMultiply:		;[Param GX, returns AX]
	call parseValue
parseMultiply2:
	load bx, gx
	je bx, 42, parseMultiplyStar
	je bx, 47, parseMultiplySlash
	je bx, 37, parseMultiplyPercent
	return
parseMultiplyStar:
	add gx, 1
	move ex, ax
	move ax, 3
	call allocBytes
	je ax, 0, infloop
	store ex, ax+1
	move bx, 4		;Multiplication
	store bx, ax
	push ax
	call parseValue
	pop ex
	store ax, ex+2
	move ax, ex
	jump parseMultiply2
parseMultiplySlash:
	add gx, 1
	move ex, ax
	move ax, 3
	call allocBytes
	je ax, 0, infloop
	store ex, ax+1
	move bx, 5		;Division
	store bx, ax
	push ax
	call parseValue
	pop ex
	store ax, ex+2
	move ax, ex
	jump parseMultiply2
parseMultiplyPercent:
	add gx, 1
	move ex, ax
	move ax, 3
	call allocBytes
	je ax, 0, infloop
	store ex, ax+1
	move bx, 6		;Modulus
	store bx, ax
	push ax
	call parseValue
	pop ex
	store ax, ex+2
	move ax, ex
	jump parseMultiply2


parseValue:			;[Param GX, returns AX]
	load bx, gx
	jne bx, 40, parseValueNumber
	add gx, 1
	call parseAdd
	add gx, 1
	return
parseValueNumber:
	move ax, gx
	call parseNumber
	move gx, ex
	move ex, ax
	move ax, 2
	call allocBytes
	je ax, 0, infloop
	store ex, ax+1
	move bx, 1		;Number
	store bx, ax
	return


parseNumber:		;[Param AX, returns AX, uses AX-EX]
	move ex, ax
	move ax, 0
	move dx, 0
parseDigit:
	load bx, ex
	je bx, 0x2D, parseNeg
	jl bx, 0x30, parseDone
	jg bx, 0x39, parseDone
	sub bx, 0x30
	move cx, ax
	shl ax, 3
	add ax, cx
	add ax, cx
	add ax, bx
	or dx, 1
	add ex, 1
	jump parseDigit
parseNeg:
	jne dx, 0, parseDone
	move dx, 2
	jump parseDigit
parseDone:
	jne dx, 3, parseRet
	neg ax
parseRet:
	return


printNumber:		;[Param AX, uses AX-DX]
	move dx, 0
	jnl ax, dx, print5p
	neg ax
	move cx, 0x2D
	out cx, 0
print5p:
	move bx, 10000
	jl ax, bx, print4p
	move cx, 0
	move dx, 0x30
print5:
	add cx, 1
	sub ax, bx
	jnl ax, bx, print5
	add cx, 0x30
	out cx, 0
print4p:
	move bx, 1000
	jl ax, bx, print4c
	move cx, 0
	move dx, 0x30
print4:
	add cx, 1
	sub ax, bx
	jnl ax, bx, print4
	add cx, 0x30
	out cx, 0
	jump print3p
print4c:
	je dx, 0, print3p
	out dx, 0
print3p:
	move bx, 100
	jl ax, bx, print3c
	move cx, 0
	move dx, 0x30
print3:
	add cx, 1
	sub ax, bx
	jnl ax, bx, print3
	add cx, 0x30
	out cx, 0
	jump print2p
print3c:
	je dx, 0, print2p
	out dx, 0
print2p:
	move bx, 10
	jl ax, bx, print2c
	move cx, 0
print2:
	add cx, 1
	sub ax, bx
	jnl ax, bx, print2
	add cx, 0x30
	out cx, 0
	jump print1
print2c:
	je dx, 0, print1
	out dx, 0
print1:
	add ax, 0x30
	out ax, 0
	return


getString:		;[Param AX, returns AX, uses AX-CX]
	move cx, ax
getInput:
	in bx, 0
	je bx, 0, getInput
	je bx, 8, goBack
	store bx, ax
	je bx, 0xA, doneInput
goNext:
	add ax, 1
	jump getInput
goBack:
	sub ax, 1
	jnl ax, cx, goBack2
	move ax, cx
goBack2:
	move bx, 0
	store bx, ax
	jump getInput
doneInput:
	move bx, 0
	store bx, ax
	sub ax, cx
	return


printString:		;[Param AX, uses AX-BX]
	load bx, ax
	je bx, 0, printDone
	out bx, 0
	add ax, 1
	jump printString
printDone:
	return


copyBytes:		;[Params AX-CX, uses AX-DX]
	add cx, ax
copyNext:
	jnl ax, cx, copyDone
	load dx, ax
	store dx, bx
	add ax, 1
	add bx, 1
	jump copyNext
copyDone:
	return


fillBytes:		;[Params AX-CX, uses AX-CX]
	add cx, ax
	jnl ax, cx, fillDone
fillNext:
	store bx, ax
	add ax, 1
	jl ax, cx, fillNext
fillDone:
	return


allocInit:		;[No parameters, uses AX-BX]
	move bx, 0xAAAA
	store bx, heap_protect
	move ax, heap_end
	and ax, 0xFFFE	;Clear smallest bit
	store ax, heap
	move bx, 0
	store bx, ax
	return


allocBytes:		;[Param AX, returns AX, uses AX-DX]
	move bx, heap
allocNext:
	load cx, bx
	and cx, 1
	je cx, 0, allocTake
allocInc:
	load bx, bx	;Follow link
	and bx, 0xFFFE	;Clear smallest bit
	jne bx, 0, allocNext
	move ax, 0
	return
allocTake:
	load cx, bx
	move dx, cx
	sub dx, bx+1
	jl dx, ax, allocInc
	jng dx, ax+4, allocMark
allocSplit:
	add ax, bx+2
	and ax, 0xFFFE	;Clear smallest bit
	store cx, ax	;Update split link
	move cx, ax
allocMark:
	or cx, 1		;Set smallest bit
	store cx, bx	;Update link
allocDone:
	move ax, bx+1
	return


freeBytes:		;[Param AX, uses AX-CX]
	sub ax, 1	;Get address of data marker (see above allocDone)
	load bx, ax
	and bx, 0xFFFE	;Clear smallest bit
	store bx, ax	;Put back, memory is now marked "free"

	return


checkHeapSmash:		;[No parameters, may not return, uses AX-BX]
	load ax, heap_protect
	move bx, 0xAAAA
	jne ax, bx, heapHalt
	return


heapHalt:
	jump heapHalt


stack:
	@add 64		; Reserve 64 words of stack space


@align 2
heap_protect:
	dw 0x5555	; Alternating 010101... will go here
heap_cache:
	dw 0
heap:

@add 0x6000
heap_end:
