PYTHON = /opt/homebrew/bin/python3
QAS = /Users/alape/Projects/quirky_toolchain/qas/qas.py

LLR_OBJ = llr.qo
LLR_SRC = llr/simio.s llr/vgi.s llr/irq.s


llr: $(LLR_OBJ)

$(LLR_OBJ): $(LLR_SRC)
	$(PYTHON) $(QAS) --object $(LLR_OBJ) $(LLR_SRC)

