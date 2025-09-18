BUILD_FOLDER = build
QAS = ../qas/qas.py
CFG2MAKE = ../qas/emulation/configs/cfg2make.py
QSIM_CFG_FOLDER = ../qas/emulation/configs
QSIM_CFG_INCLUDE = $(BUILD_FOLDER)/qsim_cfg

QSIM_CONFIG = modern

LLR_OBJ = $(BUILD_FOLDER)/llr.qo
LLR_SRC = llr/simio.s llr/vgi.s llr/irq.s

ifeq ($(OS), Windows_NT)
	PYTHON = python
else
	PYTHON = python3
endif


$(QSIM_CFG_INCLUDE):
	$(PYTHON) $(CFG2MAKE) $(QSIM_CFG_FOLDER)/$(QSIM_CONFIG).json > $(QSIM_CFG_INCLUDE)

$(LLR_OBJ): $(LLR_SRC) $(QSIM_CFG_INCLUDE)
	$(PYTHON) $(QAS) $(file < $(QSIM_CFG_INCLUDE)) --object $(LLR_OBJ) $(LLR_SRC)

llr: $(LLR_OBJ)

ifeq ($(OS), Windows_NT)
clean:
	del $(BUILD_FOLDER)\*.qo
	del $(subst /,\,$(QSIM_CFG_INCLUDE))
else
clean:
	rm  $(BUILD_FOLDER)/*.qo $(QSIM_CFG_INCLUDE)
endif
